#pragma once
#include "event_decoder.hpp"

namespace nexmon_board {
struct AdaptiveConfig {
    Config source;
    // Experimental input limits, not a claim about pose accuracy. Learned
    // tolerance is based on common-event residuals and observed packet spacing.
    std::int64_t max_skew_us=5000, max_wait_us=12000;
    std::int64_t max_age_us=250000, max_window_span_us=100000;
    unsigned max_sequence_skew=1;
};
struct AdaptiveWindow {
    JointWindow window;
    std::uint64_t alignment_version=0;
    std::array<std::array<std::int64_t,20>,3> sequences{};
    std::array<std::int64_t,3> tolerance_us{};
    std::uint32_t approximate_points=0;
    std::int64_t max_skew_us=0, span_us=0;
};
struct AdaptiveDiagnostics {
    std::uint64_t exact_windows=0, approximate_windows=0, approximate_points=0;
    std::uint64_t skipped_points=0, expired_windows=0, ready_dropped=0;
    std::uint64_t shadow_fits=0, shadow_rejected=0, switches=0, alignment_version=0;
    std::array<std::uint64_t,3> decoder_resets{};
    std::array<std::size_t,3> queued_events{};
    std::array<std::int64_t,3> tolerance_us{};
    std::array<NodeSummary,3> nodes{};
    std::uint32_t partial_points=0;
    ContinuityDiagnostic last_continuity{};
};

// One input-worker owner. Shadow fitting runs on that worker, independently of
// the inference thread. Models are immutable for all 20 points of a window;
// a pending fit may commit only before the first point of the NEXT window.
class AdaptiveIngress {
public:
    explicit AdaptiveIngress(AdaptiveConfig config);
    ~AdaptiveIngress();
    void feed(std::size_t receiver, std::string_view session,
              std::int64_t capture_us, std::uint16_t port,
              const std::uint8_t* payload, std::size_t size, std::int64_t observed_us);
    void poll(std::int64_t observed_us);
    std::vector<AdaptiveWindow> take_ready();
    AdaptiveDiagnostics diagnostics() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace nexmon_board
