#pragma once
#include <cstddef>
#include <cstdint>
#include <thread>
namespace pose::resident_sequence {
struct Stage {const char* name;size_t offset,count;uint64_t period;};
// Stage transitions only; never owns or reopens hardware, fixtures or timers.
class Sequence {
    const std::thread::id owner_=std::this_thread::get_id();
    size_t phase_=0,completed_=0;bool active_=false,failed_=false;
    void owner()const;
public:
    Stage begin();
    size_t invocation()const;
    void completeCall();
    void advance();
    void stop();
    bool done()const;
};
}
