#pragma once
#include <cstdint>
#include <limits>
#include <stdexcept>
namespace pose::producer_schedule {
inline constexpr unsigned count=100;
inline constexpr uint64_t period=20000000000ULL/101;
inline uint64_t due(uint64_t epoch,unsigned i){
    if(i>=count){throw std::runtime_error("Fixed invocation count exceeded");}
    const auto delta=20000000000ULL*i/101;
    if(epoch>std::numeric_limits<uint64_t>::max()-delta-period){throw std::runtime_error("Schedule overflow");}
    return epoch+delta;
}
inline bool inSlot(uint64_t planned,uint64_t actual){return actual>=planned&&actual-planned<period;}
}
