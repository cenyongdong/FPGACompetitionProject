#pragma once
#include "reference.hpp"
#include <deque>

namespace pose::vitals {
struct StreamUpdate {
    std::uint64_t session=0, sequence=0, first_ns=0, last_ns=0;
    std::size_t buffered=0, resets=0;
    Result result;
};
// One independent consumer; feed from an owned bounded queue, never the SDK
// thread. No stale estimate is carried through a gap, reset or missing sample.
class PhaseStream {
    Config config_;
    PhaseClock clock_;
    std::string evidence_;
    CorrelationBackend* backend_;
    std::deque<PhaseSample> ring_;
    std::uint64_t session_=0;
    std::size_t needed_=0, since_=0, stride_=0, resets_=0;
public:
    PhaseStream(PhaseClock, std::string evidence, Config={}, CorrelationBackend* =nullptr);
    StreamUpdate push(std::uint64_t session, const PhaseSample&);
    // The live owner calls this on source silence/disconnect or queue overflow.
    // It returns an empty result immediately, even before another sample arrives.
    StreamUpdate invalidate(const std::string& reason="source_unavailable");
    std::size_t buffered() const noexcept { return ring_.size(); }
};
}
