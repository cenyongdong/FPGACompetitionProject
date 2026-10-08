#include "process_window_input.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace pose::measurement {
TimedWindowInput::TimedWindowInput():receiver_("192.168.126.49",39001,5000,1){std::cout<<"INPUT_READY 39001"<<std::endl;}
std::optional<pose_v1::transport::Item> TimedWindowInput::next(){
    auto deadline=pose_v1::transport::Clock::now()+std::chrono::seconds(5);
    while(pose_v1::transport::Clock::now()<deadline){
        auto item=receiver_.pop(std::chrono::milliseconds(100));receiver_.check();
        if(receiver_.stats().rejected)throw std::runtime_error("Rejected timing CSI record");
        if(item){++consumed_;return item;}
        if(receiver_.finished())return {};
    }throw std::runtime_error("Timing complete window exceeds5s");
}
void TimedWindowInput::finish(const std::filesystem::path& out,bool all,size_t expected){
    if(!receiver_.finished())throw std::runtime_error("Timing input not finished");
    receiver_.stop();receiver_.check();const auto s=receiver_.stats();
    std::ofstream f(out/"input-summary.json");f<<"{\"sessions\":"<<s.sessions<<",\"received\":"<<s.received<<",\"consumed\":"<<consumed_<<",\"overwritten\":"<<s.overwritten<<",\"rejected\":"<<s.rejected<<",\"reconnect_discarded\":"<<s.reconnect_discarded<<"}\n";f.close();
    if(!f||s.sessions!=1||s.received!=expected||s.rejected||s.reconnect_discarded||s.received!=consumed_+s.overwritten||(all&&consumed_!=expected))throw std::runtime_error("Timing transport accounting differs");
}
}
