#pragma once
#include <array>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>
#include <string_view>
#include <vector>

// Bounded one-job adapter, independent of sockets, model preprocessing and SDK.
// Session and receiver labels are supplied by a trusted acquisition controller;
// NMD3 itself does not carry either label or a common hardware clock.
namespace nexmon_board {
constexpr std::size_t csi_values = 3 * 3 * 20 * 30;
constexpr std::size_t piwcsi2_bytes = 32 + csi_values * 16;
constexpr std::array<int, 30> ht20_ng2 = {
    -28,-26,-24,-22,-20,-18,-16,-14,-12,-10,-8,-6,-4,-2,-1,
    1,3,5,7,9,11,13,15,17,19,21,23,25,27,28};

struct Config {
    std::string session_id;
    std::array<std::string,3> receiver_ids;
    std::array<std::uint8_t,6> transmitter_mac{};
    std::uint16_t chanspec = 0;
    std::size_t expected_events = 3000; // one <=10 s, 300 Hz job; no sequence reuse
    std::array<double,3> gains{}; // mandatory finite positive candidate scales
    bool streaming = false; // rolling four-second history; original finite mode unchanged
};

struct JointWindow {
    std::int64_t start_reference_slot = 0;
    std::uint64_t source_time_ns = 0; // RX1 capture clock of the final selected event
    // External R/A/T/N = [3,3,20,30]. No interpolation or node duplication.
    std::array<std::complex<double>,csi_values> csi{};
    std::array<std::array<std::uint32_t,20>,3> event_indices{};
};
struct WindowDecision {
    std::int64_t start_reference_slot = 0;
    bool valid = false;
    bool missing_cell = false, point_error = false, different_event = false;
};
struct NodeSummary {
    std::size_t packets=0, complete_events=0, retained=0, retransmissions=0;
    std::size_t invalid_events=0, pairing_errors=0, incomplete_groups=0;
    std::size_t clock_resets=0, wraps=0;
    bool locked=false, trailing_unpaired=false;
    std::size_t trailing_cores=0;
    std::int64_t phase_scaled=0, calibration_end_us=0;
    double concentration=0;
};
struct BatchResult {
    std::string session_id;
    std::array<NodeSummary,3> nodes{};
    std::array<std::int64_t,3> slot_shifts{};
    std::size_t common_events=0;
    std::vector<WindowDecision> decisions;
    std::vector<JointWindow> windows;
    // A successful bounded association does NOT prove shared clock/phase,
    // absolute RF power, trained-model accuracy, or steady-state readiness.
};

class Ingress {
public:
    explicit Ingress(Config config);
    ~Ingress();
    Ingress(Ingress&&) noexcept;
    Ingress& operator=(Ingress&&) noexcept;
    Ingress(const Ingress&)=delete;
    Ingress& operator=(const Ingress&)=delete;
    // Per receiver, preserve original cross-port CSI/NMD3 order. Arrival time
    // is monotonic router capture time, microseconds, only a continuity guard.
    // Separate unordered UDP sockets are NOT a supported transport contract.
    void feed(std::size_t receiver, std::string_view session,
              std::int64_t arrival_us, std::uint16_t port,
              const std::uint8_t* payload, std::size_t size);
    void expire(std::size_t receiver, std::int64_t arrival_us);
    // Consume windows finalized by all three receiver watermarks. Called
    // after feed/expire, so output can begin before this bounded job ends.
    std::vector<JointWindow> take_ready();
    // Exactly once. Unfinished tail is discarded, never padded. Ambiguous
    // identity/clock/session fails the batch; start a new explicit session.
    // Result includes ALL accepted windows for deterministic replay auditing;
    // do not send them again if already consumed through take_ready().
    BatchResult finish();
    // Current retained objects, not cumulative traffic counts.
    std::array<std::size_t,3> retained_events() const;
    std::array<std::size_t,3> retained_cells() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

std::vector<std::uint8_t> encode_piwcsi2(const JointWindow& window,
    std::uint64_t frame_id, std::uint64_t source_time_ns);
std::complex<double> decode_acphy(std::uint32_t word);
} // namespace nexmon_board
