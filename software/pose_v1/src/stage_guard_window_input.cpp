#include "process_window_input.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>

namespace pose::measurement {
TimedWindowInput::TimedWindowInput(const std::filesystem::path& out):receiver_("192.168.126.49",39001,5000,1),evidence_(out){std::cout<<"INPUT_READY 39001"<<std::endl;}
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
    const auto s=receiver_.stopAndStats();receiver_.check();
    std::ofstream f(out/"input-summary.json");f<<"{\"sessions\":"<<s.sessions<<",\"received\":"<<s.received<<",\"consumed\":"<<consumed_<<",\"overwritten\":"<<s.overwritten<<",\"rejected\":"<<s.rejected<<",\"reconnect_discarded\":"<<s.reconnect_discarded<<",\"returned\":"<<returned_<<",\"final_after_join\":true,\"failure_path\":false}\n";f.close();saved_=true;
    if(!f||s.sessions!=1||s.received!=expected||s.rejected||s.reconnect_discarded||s.received!=consumed_+s.overwritten||(all&&consumed_!=expected))throw std::runtime_error("Timing transport accounting differs");
}
}

namespace pose::measurement {
void TimedWindowInput::saveStats(bool failure){const auto s=receiver_.stopAndStats();std::ofstream f(evidence_/"input-summary.json");
    f<<"{\"sessions\":"<<s.sessions<<",\"received\":"<<s.received<<",\"consumed\":"<<consumed_<<",\"returned\":"<<returned_<<",\"overwritten\":"<<s.overwritten<<",\"rejected\":"<<s.rejected<<",\"reconnect_discarded\":"<<s.reconnect_discarded<<",\"final_after_join\":true,\"failure_path\":"<<(failure?"true":"false")<<"}\n";f.close();if(!f)throw std::runtime_error("Failure input summary write failed");saved_=true;}
TimedWindowInput::~TimedWindowInput(){if(!saved_)try{saveStats(true);}catch(...){} }
}
