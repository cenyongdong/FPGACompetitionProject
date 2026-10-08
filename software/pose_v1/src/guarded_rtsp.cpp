#include "guarded_rtsp.hpp"
#include <sys/socket.h>
#include <liveMedia.hh>
#include <BasicUsageEnvironment.hh>
#include <chrono>
#include <cstring>
#include <fstream>
#include <memory>
#include <set>
#include <stdexcept>

namespace pose::stream {
namespace {
void check(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
class Source;
struct State{
    AccessUnitChannel& channel;GuardedRtspOptions options;std::ofstream log;
    TaskScheduler* scheduler=nullptr;UsageEnvironment* env=nullptr;RTSPServer* server=nullptr;
    EventLoopWatchVariable done{0};TaskToken deadline=nullptr,finish=nullptr;
    std::set<Source*> sources;std::exception_ptr failure;
    Bytes sps,pps;uint64_t nextSource=0,pictures=0;
    std::chrono::steady_clock::time_point origin=std::chrono::steady_clock::now();timeval wall{};
    State(AccessUnitChannel& c,const GuardedRtspOptions& o,const std::filesystem::path& path):channel(c),options(o),log(path/"events.jsonl"){check(bool(log),"RTSP log failed");gettimeofday(&wall,nullptr);}
    void fail(){failure=std::current_exception();done=1;}
};
class Source final:public FramedSource{
    State& state_;uint64_t id_;std::deque<std::shared_ptr<const AccessUnit>> queue_;unsigned phase_=0;bool joined_=false;
    void doGetNextFrame()override{send();}
    void send(){
        if(!isCurrentlyAwaitingData()||queue_.empty())return;
        try{
            const auto& unit=*queue_.front();const auto& nal=phase_==0?unit.sps:phase_==1?unit.pps:unit.slice;
            check(nal.size()<=fMaxSize,"RTSP NAL truncation forbidden");fFrameSize=nal.size();fNumTruncatedBytes=0;
            std::memcpy(fTo,nal.data(),nal.size());
            // Producer PTS is relative to its sample epoch; a fixed wall epoch
            // is used only for RTCP presentation mapping. RTP deltas stay real.
            const auto wallUs=int64_t(state_.wall.tv_sec)*1000000+state_.wall.tv_usec+unit.ptsUs;
            fPresentationTime.tv_sec=wallUs/1000000;fPresentationTime.tv_usec=wallUs%1000000;fDurationInMicroseconds=0;
            state_.log<<"{\"event\":\"nal_delivered\",\"source\":"<<id_<<",\"encoded_id\":"<<unit.id<<",\"pts_us\":"<<unit.ptsUs<<",\"type\":"<<(nal[0]&31)<<",\"bytes\":"<<nal.size()<<"}"<<std::endl;
            if(phase_<2)++phase_;else{queue_.pop_front();phase_=queue_.empty()||queue_.front()->idr?0:2;}
            FramedSource::afterGetting(this);
        }catch(...){state_.fail();handleClosure();}
    }
public:
    Source(UsageEnvironment& env,State& s):FramedSource(env),state_(s),id_(s.nextSource++){state_.sources.insert(this);state_.log<<"{\"event\":\"source_created\",\"source\":"<<id_<<"}"<<std::endl;}
    ~Source()override{state_.sources.erase(this);state_.log<<"{\"event\":\"source_closed\",\"source\":"<<id_<<"}"<<std::endl;}
    unsigned maxFrameSize()const override{return 262144;}
    void publish(std::shared_ptr<const AccessUnit> u){
        if(!joined_&&!u->idr)return;
        if(!joined_){joined_=true;phase_=0;}
        check(queue_.size()<AccessUnitChannel::capacity,"Slow RTSP client exceeded AU capacity");
        if(queue_.empty())phase_=u->idr?0:2;
        queue_.push_back(std::move(u));send();
    }
};
void sendError(void* p){
    auto& state=*static_cast<State*>(p);
    state.log<<"{\"event\":\"rtp_send_error\",\"action\":\"stop_reference_chain\"}"<<std::endl;
    try{throw std::runtime_error("RTP transport send failed; stop reference chain");}catch(...){state.fail();}
}
class Session final:public OnDemandServerMediaSubsession{
    State& state_;std::string aux_;
    FramedSource* createNewStreamSource(unsigned,unsigned& bitrate)override{
        bitrate=2000;
        if(state_.sources.size()>=state_.options.maximumClients)return nullptr;
        return H264VideoStreamDiscreteFramer::createNew(envir(),new Source(envir(),state_),False,False);
    }
    RTPSink* createNewRTPSink(Groupsock* gs,unsigned char pt,FramedSource*)override{
        auto* sink=H264VideoRTPSink::createNew(envir(),gs,pt,state_.sps.data(),state_.sps.size(),state_.pps.data(),state_.pps.size());
        check(sink!=nullptr,"RTP sink creation failed");sink->setOnSendErrorFunc(sendError,&state_);return sink;
    }
    void getStreamParameters(unsigned clientId,const sockaddr_storage& clientAddress,const Port& clientRTP,const Port& clientRTCP,
        int tcpSocket,unsigned char rtpChannel,unsigned char rtcpChannel,TLSState* tls,sockaddr_storage& destination,
        u_int8_t& ttl,Boolean& multicast,Port& serverRTP,Port& serverRTCP,void*& token)override{
        OnDemandServerMediaSubsession::getStreamParameters(clientId,clientAddress,clientRTP,clientRTCP,tcpSocket,rtpChannel,rtcpChannel,tls,destination,ttl,multicast,serverRTP,serverRTCP,token);
        check(tcpSocket>=0,"Guarded gate supports TCP only");int bytes=state_.options.sendBufferBytes;
        check(setsockopt(tcpSocket,SOL_SOCKET,SO_SNDBUF,&bytes,sizeof(bytes))==0,"TCP send buffer cap failed");
        socklen_t length=sizeof(bytes);check(getsockopt(tcpSocket,SOL_SOCKET,SO_SNDBUF,&bytes,&length)==0,"TCP send buffer readback failed");
        check(bytes>=int(state_.options.sendBufferBytes)&&bytes<=int(2*state_.options.sendBufferBytes),"TCP send buffer bound differs");
        state_.log<<"{\"event\":\"TCP_buffer_bound\",\"requested\":"<<state_.options.sendBufferBytes<<",\"actual\":"<<bytes<<"}"<<std::endl;
    }
    const char* getAuxSDPLine(RTPSink* sink,FramedSource*)override{
        if(aux_.empty()){const char* s=sink->auxSDPLine();check(s,"Actual SDP parameter sets missing");aux_=s;}return aux_.c_str();
    }
public:Session(UsageEnvironment& env,State& s):OnDemandServerMediaSubsession(env,False),state_(s){}
};
void stop(void* p){static_cast<State*>(p)->done=1;}
void timeout(void* p){auto& s=*static_cast<State*>(p);s.deadline=nullptr;try{throw std::runtime_error("Finite RTSP deadline exceeded");}catch(...){s.fail();}}
void available(void* p,int){
    auto& s=*static_cast<State*>(p);
    try{
        auto batch=s.channel.take();
        for(auto& unit:batch.units){
            if(s.sps.empty()){
                check(unit.idr,"RTSP first AU must be IDR");s.sps=unit.sps;s.pps=unit.pps;
                auto* media=ServerMediaSession::createNew(*s.env,"pose","pose","Owned live producer access units");media->addSubsession(new Session(*s.env,s));s.server->addServerMediaSession(media);
                s.log<<"{\"event\":\"ready\",\"port\":"<<s.options.port<<",\"owned_AU\":true}"<<std::endl;
            }
            check(unit.sps==s.sps&&unit.pps==s.pps,"RTSP parameter set changed");
            s.log<<"{\"event\":\"au_received\",\"encoded_id\":"<<unit.id<<",\"pts_us\":"<<unit.ptsUs<<",\"idr\":"<<(unit.idr?"true":"false")<<"}"<<std::endl;++s.pictures;
            auto owned=std::make_shared<const AccessUnit>(std::move(unit));
            const std::vector<Source*> subscribers(s.sources.begin(),s.sources.end());
            for(auto* source:subscribers){source->publish(owned);if(s.failure)break;}
            if(s.failure)std::rethrow_exception(s.failure);
        }
        if(batch.closed&&!s.finish){s.scheduler->disableBackgroundHandling(s.channel.notificationFd());s.finish=s.scheduler->scheduleDelayedTask(1000000,stop,&s);}
    }catch(...){s.fail();}
}
}
void serveGuardedAccessUnits(AccessUnitChannel& channel,const GuardedRtspOptions& options,const std::filesystem::path& out){
    check(options.sendBufferBytes>=32768&&options.sendBufferBytes<=262144,"TCP buffer option invalid");
    check(options.port>=1024&&options.port<=65535&&options.maximumSeconds>=1&&options.maximumSeconds<=180&&options.maximumClients>=1&&options.maximumClients<=2,"RTSP finite options invalid");
    check(!std::filesystem::exists(out),"Preserve RTSP evidence");std::filesystem::create_directory(out);State state(channel,options,out);
    try{
        OutPacketBuffer::maxSize=262144;state.scheduler=BasicTaskScheduler::createNew();state.env=BasicUsageEnvironment::createNew(*state.scheduler);
        state.server=RTSPServer::createNew(*state.env,options.port,nullptr,10);check(state.server,"RTSP bind/create failed");
        state.scheduler->setBackgroundHandling(channel.notificationFd(),SOCKET_READABLE,available,&state);
        state.deadline=state.scheduler->scheduleDelayedTask(int64_t(options.maximumSeconds)*1000000,timeout,&state);
        state.scheduler->doEventLoop(&state.done);
    }catch(...){state.failure=std::current_exception();}
    if(state.scheduler){state.scheduler->disableBackgroundHandling(channel.notificationFd());state.scheduler->unscheduleDelayedTask(state.deadline);state.scheduler->unscheduleDelayedTask(state.finish);}
    if(state.server)Medium::close(state.server);
    state.log<<"{\"event\":\"completed\",\"pictures\":"<<state.pictures<<",\"sources_created\":"<<state.nextSource<<",\"sources_live\":"<<state.sources.size()<<",\"failed\":"<<(state.failure?"true":"false")<<"}"<<std::endl;
    if(state.env)state.env->reclaim();
    delete state.scheduler;
    if(state.failure)std::rethrow_exception(state.failure);
    check(state.sources.empty(),"RTSP sources leaked");
}
}
