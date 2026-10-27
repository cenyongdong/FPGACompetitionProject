#pragma once
#include "preprocess.hpp"
#include <deque>

namespace pose_v1 {
using PhaseHints = std::array<std::array<std::uint8_t,kTimes>,kReceivers>;
struct PhaseSampleIdentity {
    std::uint64_t epoch=0, sample=0;
    std::int64_t time_ns=0; // per-RX monotonic source time, never cross-RX subtraction
};
struct PhaseBranchDiagnostic {
    std::uint64_t samples=0, reused=0, resets=0, branch_changes=0, undefined=0;
};
struct PhaseBranchHint {
    std::uint8_t rotation=0; // -2*pi/3 * rotation, reduced modulo 3
    bool reset=false, reused=false, defined=true;
};

// Observe each physical RX event in its source order before window selection.
// An immutable event may be reused by overlapping windows within a bounded
// 128-event cache without advancing phase state again. No CSI is modified.
class PhaseBranchTracker {
public:
    explicit PhaseBranchTracker(std::int64_t max_gap_ns=10000000);
    PhaseBranchHint observe(std::size_t receiver,const std::array<std::complex<double>,3>& first_carrier,
                            PhaseSampleIdentity identity);
    void reset(std::size_t receiver);
    void reset();
    PhaseBranchDiagnostic diagnostics(std::size_t receiver)const;
private:
    struct Entry {
        PhaseSampleIdentity id;
        std::array<std::complex<double>,3> reference;
        PhaseBranchHint hint;
    };
    struct State {
        bool have=false;
        PhaseSampleIdentity last;
        std::array<double,2> previous{};
        std::array<int,2> winding{};
        std::deque<Entry> cache;
        PhaseBranchDiagnostic diagnostic;
    };
    std::array<State,3> states_;
    std::int64_t max_gap_ns_;
};

// Original numerical pipeline runs exactly once. The optional transform only
// changes its phase channels; zero-rotation channels remain bitwise untouched.
Tokens apply_phase_branches(const Tokens& original,const PhaseHints& hints);
} // namespace pose_v1
