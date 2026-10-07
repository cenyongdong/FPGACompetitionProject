// Finite, SDK/VPU-independent replay of verified owned H.264 NALs and capture PTS.
#include <liveMedia.hh>
#include <BasicUsageEnvironment.hh>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace {
using Clock=std::chrono::steady_clock;
constexpr unsigned FrameCount=54, PeriodUs=100000, MaxNal=262144;
void require(bool ok,const char* text) { if(!ok) throw std::runtime_error(text); }
struct Picture { unsigned id; long long pts; std::vector<unsigned char> nal; bool idr; };
struct Data {
    std::vector<unsigned char> sps,pps;
    std::vector<Picture> pictures;
    Data(const char* blob,const char* index) {
        const auto size=std::filesystem::file_size(blob);
        require(size>0 && size<=4*1024*1024,"H264 blob capacity");
        std::vector<unsigned char> bytes(size);
        std::ifstream input(blob,std::ios::binary);
        require(bool(input.read(reinterpret_cast<char*>(bytes.data()),bytes.size())),"H264 read");
        std::ifstream rows(index); require(bool(rows),"Index open");
        std::string line; unsigned offset=0;
        while(std::getline(rows,line)) {
            std::istringstream row(line); std::string kind,extra; long long pts; unsigned begin,length,type;
            require(bool(row>>kind>>pts>>begin>>length>>type) && !(row>>extra),"Index row");
            require(begin==offset && length>0 && length<=MaxNal && begin<=bytes.size() && length<=bytes.size()-begin,"Index bounds");
            // Index refers to complete NAL payloads preceded by exact Annex B prefixes.
            require(length>=5 && bytes[begin]==0 && bytes[begin+1]==0 && bytes[begin+2]==0 && bytes[begin+3]==1,"Annex B prefix");
            std::vector<unsigned char> nal(bytes.begin()+begin+4,bytes.begin()+begin+length);
            require(!(nal[0]&0x80) && (nal[0]&31)==type,"NAL type");
            if(kind=="SPS") {require(sps.empty() && type==7 && pictures.empty(),"SPS record");sps=std::move(nal);}
            else if(kind=="PPS") {require(pps.empty() && type==8 && pictures.empty(),"PPS record");pps=std::move(nal);}
            else {
                require(kind=="FRAME" && (type==1 || type==5) && pictures.size()<FrameCount,"Picture record");
                require(!sps.empty() && !pps.empty() && pts==static_cast<long long>(pictures.size())*PeriodUs,"Capture PTS");
                // first_mb_in_slice==0 (UE code '1'); reject additional slices in this contract.
                require(nal.size()>1 && (nal[1]&0x80),"Unsupported multi-slice picture");
                pictures.push_back({static_cast<unsigned>(pictures.size()),pts,std::move(nal),type==5});
            }
            offset+=length;
        }
        require(offset==bytes.size() && pictures.size()==FrameCount && pictures[0].idr,"Index coverage");
    }
};
struct State {
    const Data& data; std::ofstream& log;
    Clock::time_point origin=Clock::now(); timeval wall{};
    EventLoopWatchVariable done{0}; TaskToken stopToken=nullptr;
    bool failed=false; unsigned sources=0,nextSource=0;
    State(const Data& d,std::ofstream& l):data(d),log(l) {gettimeofday(&wall,nullptr);}
    long long elapsed() const {return std::chrono::duration_cast<std::chrono::microseconds>(Clock::now()-origin).count();}
    void fail(const char* reason) {log<<"{\"event\":\"failure\",\"reason\":\""<<reason<<"\"}"<<std::endl;failed=true;done=1;}
};
class Source final:public FramedSource {
    State& state_; unsigned sourceId_; unsigned long long absoluteFrame_; unsigned phase_=0;
    static void deliver(void* p) {static_cast<Source*>(p)->send();}
    void send() {
        nextTask()=nullptr;
        const auto& pic=state_.data.pictures[absoluteFrame_%FrameCount];
        const auto& nal=phase_==0 ? state_.data.sps : phase_==1 ? state_.data.pps : pic.nal;
        if(nal.size()>fMaxSize) {state_.fail("NAL exceeds live555 buffer");handleClosure();return;}
        fFrameSize=nal.size();fNumTruncatedBytes=0;std::memcpy(fTo,nal.data(),nal.size());
        const auto pts=absoluteFrame_*PeriodUs;
        const auto wallUs=static_cast<unsigned long long>(state_.wall.tv_sec)*1000000+state_.wall.tv_usec+pts;
        fPresentationTime.tv_sec=wallUs/1000000;fPresentationTime.tv_usec=wallUs%1000000;
        fDurationInMicroseconds=phase_==2 ? PeriodUs:0;
        state_.log<<"{\"event\":\"nal_delivered\",\"source\":"<<sourceId_<<",\"absolute_frame\":"<<absoluteFrame_
                  <<",\"encoded_frame\":"<<pic.id<<",\"pts_us\":"<<pts<<",\"type\":"<<(nal[0]&31)
                  <<",\"bytes\":"<<nal.size()<<",\"elapsed_us\":"<<state_.elapsed()<<"}"<<std::endl;
        if(phase_<2) ++phase_;
        else {++absoluteFrame_;phase_=state_.data.pictures[absoluteFrame_%FrameCount].idr ? 0:2;}
        FramedSource::afterGetting(this);
    }
    void doGetNextFrame() override {
        const auto due=static_cast<long long>(absoluteFrame_*PeriodUs);
        const auto wait=due-state_.elapsed();
        nextTask()=envir().taskScheduler().scheduleDelayedTask(wait>0 ? wait:0,deliver,this);
    }
    void doStopGettingFrames() override {envir().taskScheduler().unscheduleDelayedTask(nextTask());}
public:
    Source(UsageEnvironment& env,State& state):FramedSource(env),state_(state),sourceId_(state.nextSource++) {
        require(state.sources<2,"At most two client sources");++state.sources;
        absoluteFrame_=(state.elapsed()+PeriodUs-1)/PeriodUs;
        while(!state.data.pictures[absoluteFrame_%FrameCount].idr) ++absoluteFrame_;
        state.log<<"{\"event\":\"source_created\",\"source\":"<<sourceId_<<",\"start_absolute_frame\":"<<absoluteFrame_
                 <<",\"start_encoded_frame\":"<<absoluteFrame_%FrameCount<<",\"elapsed_us\":"<<state.elapsed()<<"}"<<std::endl;
    }
    ~Source() override {doStopGettingFrames();--state_.sources;state_.log<<"{\"event\":\"source_closed\",\"source\":"<<sourceId_<<"}"<<std::endl;}
    unsigned maxFrameSize() const override {return MaxNal;}
};
class Session final:public OnDemandServerMediaSubsession {
    State& state_; std::string aux_;
    FramedSource* createNewStreamSource(unsigned,unsigned& bitrate) override {
        bitrate=2000;
        if(state_.sources>=2) {state_.fail("Too many clients");return nullptr;}
        return H264VideoStreamDiscreteFramer::createNew(envir(),new Source(envir(),state_),False,False);
    }
    RTPSink* createNewRTPSink(Groupsock* gs,unsigned char pt,FramedSource*) override {
        return H264VideoRTPSink::createNew(envir(),gs,pt,state_.data.sps.data(),state_.data.sps.size(),state_.data.pps.data(),state_.data.pps.size());
    }
    char const* getAuxSDPLine(RTPSink* sink,FramedSource*) override {
        if(aux_.empty()) {const char* s=sink->auxSDPLine();require(s!=nullptr,"No actual SDP parameter sets");aux_=s;}
        return aux_.c_str();
    }
public:
    Session(UsageEnvironment& env,State& state):OnDemandServerMediaSubsession(env,False),state_(state) {}
};
void finish(void* p) {auto* state=static_cast<State*>(p);state->stopToken=nullptr;state->done=1;}
}
int main(int argc,char** argv) {
    TaskScheduler* scheduler=nullptr;UsageEnvironment* env=nullptr;RTSPServer* server=nullptr;
    std::unique_ptr<Data> data;std::ofstream log;std::unique_ptr<State> state;
    try {
        require(argc==5 && std::string(argv[1])=="--allow-network-replay","Usage: --allow-network-replay video.h264 index.tsv fresh-results");
        data=std::make_unique<Data>(argv[2],argv[3]);require(!std::filesystem::exists(argv[4]),"Preserve results");
        std::filesystem::create_directory(argv[4]);log.open(std::filesystem::path(argv[4])/"events.jsonl");require(bool(log),"Log open");
        state=std::make_unique<State>(*data,log);OutPacketBuffer::maxSize=MaxNal;
        scheduler=BasicTaskScheduler::createNew();env=BasicUsageEnvironment::createNew(*scheduler);
        server=RTSPServer::createNew(*env,8554,nullptr,10);require(server!=nullptr,"RTSP bind/create failed");
        auto* session=ServerMediaSession::createNew(*env,"pose","pose","Verified discrete prerecorded pose windows");
        session->addSubsession(new Session(*env,*state));server->addServerMediaSession(session);
        state->stopToken=scheduler->scheduleDelayedTask(60000000,finish,state.get());
        log<<"{\"event\":\"ready\",\"port\":8554,\"frames\":54,\"seconds\":60,\"vpu\":false,\"npu\":false,\"hdmi\":false}"<<std::endl;
        std::cout<<"READY rtsp://192.168.126.49:8554/pose"<<std::endl;
        scheduler->doEventLoop(&state->done);scheduler->unscheduleDelayedTask(state->stopToken);
        Medium::close(server);server=nullptr;
        log<<"{\"event\":\"completed\",\"sources_created\":"<<state->nextSource<<",\"sources_live\":"<<state->sources
           <<",\"elapsed_us\":"<<state->elapsed()<<",\"failed\":"<<(state->failed ? "true":"false")<<"}"<<std::endl;
        const bool failed=state->failed;require(state->sources==0,"Source ownership leak");
        env->reclaim();env=nullptr;delete scheduler;scheduler=nullptr;return failed ? 1:0;
    } catch(const std::exception& e) {
        if(server) Medium::close(server);
        if(env) env->reclaim();
        delete scheduler;
        std::cerr<<e.what()<<'\n';return 1;
    }
}
