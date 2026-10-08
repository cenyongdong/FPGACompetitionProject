#include "tcp_window_input.hpp"
#include <iostream>
#include <stdexcept>

namespace pose::input {
namespace {
void check(bool ok,const char* reason){if(!ok)throw std::runtime_error(reason);}
}
TcpWindowInput::TcpWindowInput(const std::filesystem::path& evidence)
    :receiver_("192.168.126.49",39001,5000,2),evidence_(evidence) {
    check(!std::filesystem::exists(evidence_),"Preserve TCP input evidence");
    std::filesystem::create_directory(evidence_);
    log_.open(evidence_/"received.jsonl");check(bool(log_),"TCP evidence open failed");
    std::ofstream listener(evidence_/"listener.json");
    listener<<"{\"port\":39001,\"capacity\":1,\"max_sessions\":2,\"idle_ms\":5000}\n";
    check(bool(listener),"TCP listener evidence failed");
    std::cout<<"INPUT_READY 39001"<<std::endl;
}
pose_v1::Window TcpWindowInput::next(){
    const auto deadline=pose_v1::transport::Clock::now()+std::chrono::seconds(5);
    while(pose_v1::transport::Clock::now()<deadline){
        auto item=receiver_.pop(std::chrono::milliseconds(100));receiver_.check();
        check(receiver_.stats().rejected==0,"Rejected CSI record; stop pipeline");
        if(item){
            const auto arrived=std::chrono::duration_cast<std::chrono::nanoseconds>(item->arrived.time_since_epoch()).count();
            log_<<"{\"call\":"<<consumed_++<<",\"session\":"<<item->session<<",\"sequence\":"<<item->sequence
                <<",\"frame_id\":"<<item->window.frame_id<<",\"source_time_ns\":"<<item->window.source_time_ns<<",\"arrived_ns\":"<<arrived<<"}"<<std::endl;
            check(bool(log_),"TCP record evidence write failed");return std::move(item->window);
        }
        check(!receiver_.finished(),"TCP ended before expected complete window");
    }
    throw std::runtime_error("Complete CSI window exceeds5s");
}
void TcpWindowInput::finish(size_t expected){
    // Wait for clean second-session EOF, not merely the last model result.
    const auto deadline=pose_v1::transport::Clock::now()+std::chrono::seconds(1);
    while(!receiver_.finished()&&pose_v1::transport::Clock::now()<deadline){
        check(!receiver_.pop(std::chrono::milliseconds(100)),"Unexpected extra complete window");receiver_.check();
    }
    check(receiver_.finished(),"CSI sender did not close second session");
    receiver_.stop();receiver_.check();const auto s=receiver_.stats();
    std::ofstream f(evidence_/"summary.json");
    f<<"{\"sessions\":"<<s.sessions<<",\"received\":"<<s.received<<",\"consumed\":"<<consumed_
     <<",\"rejected\":"<<s.rejected<<",\"overwritten\":"<<s.overwritten<<",\"reconnect_discarded\":"<<s.reconnect_discarded<<"}\n";
    check(bool(f),"TCP summary write failed");
    check(s.sessions==2&&s.received==expected&&consumed_==expected&&s.rejected==0&&s.overwritten==0&&s.reconnect_discarded==0,"Fixed2Hz CSI transport coverage differs");
}
}
