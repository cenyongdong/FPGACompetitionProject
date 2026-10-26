#include "pl_acf.hpp"
#include <stdexcept>
#include <thread>

namespace pose::vitals {
PlDotProducts::PlDotProducts(const std::string& profile,bool qualified,Read rd,Write wr,std::chrono::milliseconds timeout)
 :read_(std::move(rd)),write_(std::move(wr)),timeout_(timeout){
    // Reject old hardware before even the first register read.
    if(profile!="vitals-acf-v1"||!qualified)throw std::runtime_error("ACF requires a qualified new hardware identity; r45 has no ACF registers");
    if(!read_||!write_||timeout_.count()<=0||read_(0)!=0x56414301)throw std::runtime_error("ACF transport/ABI mismatch");
}
std::vector<std::int64_t> PlDotProducts::calculate(const std::vector<std::int32_t>& x,std::size_t last){
    validate_dot_input(x,last);
    if(isolated_)throw std::runtime_error("ACF backend isolated; no automatic retry");
    try{
        if(read_(4)&~2u)throw std::runtime_error("ACF not idle/healthy");
        if(seq_==0xffffffff)throw std::runtime_error("ACF sequence exhausted");
        // Command 2 only resets this local non-DMA compute block. Idle required.
        write_(8,2);if(read_(4)!=0)throw std::runtime_error("ACF local reset not complete");
        write_(0xc,std::uint32_t(x.size()));write_(0x10,std::uint32_t(last));write_(0x14,++seq_);
        for(auto v:x)write_(0x20,std::uint32_t(v));
        if(read_(0x24)!=x.size())throw std::runtime_error("ACF load count mismatch");
        write_(8,1);const auto deadline=std::chrono::steady_clock::now()+timeout_;
        for(;;){const auto status=read_(4);if(status&~3u)throw std::runtime_error("ACF hardware fault");
            if(!(status&1u)&&(status&2u)&&read_(0x18)==seq_)break;
            if(std::chrono::steady_clock::now()>=deadline)throw std::runtime_error("ACF deadline; isolate without retry or transport release");
            std::this_thread::yield();
        }
        std::vector<std::int64_t> out;out.reserve(last+1);
        for(unsigned k=0;k<=last;++k){write_(0x28,k);const auto low=read_(0x2c),high=read_(0x30);
            // High register is a sign-extended 16-bit upper accumulator word.
            const auto upper=std::int64_t(std::int32_t(high));out.push_back(upper*4294967296LL+low);
        }
        if(read_(4)!=2||read_(0x18)!=seq_)throw std::runtime_error("ACF result identity changed");
        return out;
    }catch(...){isolated_=true;throw;}
}
}
