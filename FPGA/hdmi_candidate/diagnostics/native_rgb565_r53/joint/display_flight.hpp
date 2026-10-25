#pragma once
#include <cstdint>
#include <optional>
#include <stdexcept>

// SDK-free invocation ownership for one display command in flight. The
// publisher keeps the full result until completion; this token owns no buffer.
class DisplayFlight {
    std::optional<uint64_t> invocation_;
public:
    bool active() const { return invocation_.has_value(); }
    template<class Begin> void begin(uint64_t invocation,Begin&& begin) {
        if(active())throw std::runtime_error("A display frame is already in flight");
        begin();invocation_=invocation;
    }
    template<class Poll,class Complete> bool service(Poll&& poll,Complete&& complete) {
        if(!active() || !poll())return false;
        complete(*invocation_);invocation_.reset();return true;
    }
};
