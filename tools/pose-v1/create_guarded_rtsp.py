"""Same-feature isolated variant; preserve the accepted unguarded source."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'software/pose_v1/src/guarded_rtsp.cpp';assert not target.exists()
s=(root/'software/pose_v1/src/online_rtsp.cpp').read_text()
s=s.replace('#include "online_rtsp.hpp"','#include "guarded_rtsp.hpp"\n#include <sys/socket.h>')
s=s.replace('RtspOptions','GuardedRtspOptions').replace('serveOwnedAccessUnits','serveGuardedAccessUnits')
anchor='class Session final:public OnDemandServerMediaSubsession{'
handler='''void sendError(void* p){
    auto& state=*static_cast<State*>(p);
    state.log<<"{\\\"event\\\":\\\"rtp_send_error\\\",\\\"action\\\":\\\"stop_reference_chain\\\"}"<<std::endl;
    try{throw std::runtime_error("RTP transport send failed; stop reference chain");}catch(...){state.fail();}
}
'''
assert s.count(anchor)==1;s=s.replace(anchor,handler+anchor)
anchor='''        return H264VideoRTPSink::createNew(envir(),gs,pt,state_.sps.data(),state_.sps.size(),state_.pps.data(),state_.pps.size());'''
replacement='''        auto* sink=H264VideoRTPSink::createNew(envir(),gs,pt,state_.sps.data(),state_.sps.size(),state_.pps.data(),state_.pps.size());
        check(sink!=nullptr,"RTP sink creation failed");sink->setOnSendErrorFunc(sendError,&state_);return sink;'''
assert s.count(anchor)==1;s=s.replace(anchor,replacement)
anchor='''    const char* getAuxSDPLine(RTPSink* sink,FramedSource*)override{'''
limits='''    void getStreamParameters(unsigned clientId,const sockaddr_storage& clientAddress,const Port& clientRTP,const Port& clientRTCP,
        int tcpSocket,unsigned char rtpChannel,unsigned char rtcpChannel,TLSState* tls,sockaddr_storage& destination,
        u_int8_t& ttl,Boolean& multicast,Port& serverRTP,Port& serverRTCP,void*& token)override{
        OnDemandServerMediaSubsession::getStreamParameters(clientId,clientAddress,clientRTP,clientRTCP,tcpSocket,rtpChannel,rtcpChannel,tls,destination,ttl,multicast,serverRTP,serverRTCP,token);
        check(tcpSocket>=0,"Guarded gate supports TCP only");int bytes=state_.options.sendBufferBytes;
        check(setsockopt(tcpSocket,SOL_SOCKET,SO_SNDBUF,&bytes,sizeof(bytes))==0,"TCP send buffer cap failed");
        socklen_t length=sizeof(bytes);check(getsockopt(tcpSocket,SOL_SOCKET,SO_SNDBUF,&bytes,&length)==0,"TCP send buffer readback failed");
        check(bytes>=int(state_.options.sendBufferBytes)&&bytes<=int(2*state_.options.sendBufferBytes),"TCP send buffer bound differs");
        state_.log<<"{\\\"event\\\":\\\"TCP_buffer_bound\\\",\\\"requested\\\":"<<state_.options.sendBufferBytes<<",\\\"actual\\\":"<<bytes<<"}"<<std::endl;
    }
'''
assert s.count(anchor)==1;s=s.replace(anchor,limits+anchor)
s=s.replace('check(options.port>=1024','check(options.sendBufferBytes>=32768&&options.sendBufferBytes<=262144,"TCP buffer option invalid");\n    check(options.port>=1024')
target.write_bytes(s.encode());print(target)
