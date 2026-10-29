#pragma once
#include <array>
#include <complex>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

// Bounded one-job adapter, independent of sockets, model preprocessing and SDK.
// Session and receiver labels are supplied by a trusted acquisition controller;
// NMD3 itself does not carry either label or a common hardware clock.
namespace nexmon_board {
constexpr std::size_t csi_values = 3 * 3 * 20 * 30;
constexpr std::size_t piwcsi2_bytes = 32 + csi_values * 16;
constexpr std::array<int, 30> ht20_ng2 = {-28, -26, -24, -22, -20, -18, -16, -14, -12, -10, -8, -6, -4, -2,
	-1, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 28};

struct Config {
	std::string session_id;
	std::array<std::string, 3> receiver_ids;
	std::array<std::uint8_t, 6> transmitter_mac{};
	std::uint16_t chanspec = 0;
	std::size_t expected_events = 3000; // one <=10 s, 300 Hz job; no sequence reuse
	std::array<double, 3> gains{};		// mandatory finite positive candidate scales
	bool streaming = false;				// rolling four-second history; original finite mode unchanged
	bool track_clock = false;			// resident-only causal phase slew; never changes finalized cells
};

// Recoverable capture continuity failures are distinct from malformed input or
// source identity changes. The payload has fixed size for bounded event rings;
// callers must discard this entire Ingress generation before resuming.
enum class ContinuityReason : std::uint8_t {
	arrival_backwards,
	arrival_gap,
	pairing_timeout,
	missing_metadata,
	pairing_mismatch,
	incomplete_event,
	duplicate_core,
	event_clock,
	counter_step,
	duplicate_sequence,
	reused_sequence,
	sequence_step,
	retained_clock,
	phase_lock,
	calibration_budget
};
const char* continuity_reason_name(ContinuityReason reason) noexcept;

struct ContinuityDiagnostic {
	std::uint32_t receiver = 0;
	ContinuityReason reason = ContinuityReason::arrival_gap;
	bool have_previous = false, event_clock_known = false;
	std::int64_t arrival_us = 0, previous_arrival_us = 0, host_delta_us = 0;
	std::uint16_t tsf_before = 0, tsf_after = 0, tsf_delta_us = 0;
	std::uint16_t counter_before = 0, counter_after = 0, counter_step = 0;
	std::uint16_t sequence_before = 0, sequence_after = 0;
	std::uint32_t phase_samples = 0;
	double phase_concentration = 0;
};

class ContinuityError : public std::runtime_error {
public:
	explicit ContinuityError(ContinuityDiagnostic diagnostic);

	const ContinuityDiagnostic& diagnostic() const noexcept {
		return diagnostic_;
	}

private:
	ContinuityDiagnostic diagnostic_;
};

struct JointWindow {
	std::int64_t start_reference_slot = 0;
	std::uint64_t source_time_ns = 0; // RX1 capture clock of the final selected event
	// External R/A/T/N = [3,3,20,30]. No interpolation or node duplication.
	std::array<std::complex<double>, csi_values> csi{};
	std::array<std::array<std::uint32_t, 20>, 3> event_indices{};
};

struct WindowDecision {
	std::int64_t start_reference_slot = 0;
	bool valid = false;
	bool missing_cell = false, point_error = false, different_event = false;
};

struct NodeSummary {
	std::size_t packets = 0, complete_events = 0, retained = 0, retransmissions = 0;
	std::size_t invalid_events = 0, pairing_errors = 0, incomplete_groups = 0;
	std::size_t clock_resets = 0, wraps = 0;
	bool locked = false, trailing_unpaired = false;
	std::size_t trailing_cores = 0;
	std::int64_t phase_scaled = 0, calibration_end_us = 0;
	std::int64_t phase_correction_scaled = 0, phase_step_scaled = 0, phase_residual_scaled = 0;
	std::uint64_t phase_updates = 0, phase_rejected_blocks = 0;
	std::size_t phase_samples = 0;
	double concentration = 0;
};

// Fixed-size, cumulative for this alignment generation. Rejection categories
// may overlap. Diagnostics never select, replace, or relax any input sample.
struct WindowDiagnostics {
	std::uint64_t decided = 0, accepted = 0, missing = 0, point_error = 0, different_event = 0;
	std::uint64_t rejected_streak = 0, different_points = 0;
	std::array<std::uint64_t, 3> missing_points{}, point_errors{};
	// Signed largest absolute residual in the latest finalized window, in
	// microseconds * 300. Divide by 300 for us; the original limit is 250000.
	std::array<std::int64_t, 3> last_error_scaled{};
	std::array<std::uint16_t, 3> last_mismatch_sequences{};
	std::int64_t last_window_slot = 0, last_mismatch_slot = 0;
	std::array<std::int64_t, 3> slot_shifts{};
	std::array<NodeSummary, 3> nodes{};
	bool anchored = false;
};

struct BatchResult {
	std::string session_id;
	std::array<NodeSummary, 3> nodes{};
	std::array<std::int64_t, 3> slot_shifts{};
	std::size_t common_events = 0;
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
	Ingress(const Ingress&) = delete;
	Ingress& operator=(const Ingress&) = delete;
	// Per receiver, preserve original cross-port CSI/NMD3 order. Arrival time
	// is monotonic router capture time, microseconds, only a continuity guard.
	// Separate unordered UDP sockets are NOT a supported transport contract.
	// A fresh streaming instance may join mid-event: validated metadata and
	// non-core0 CSI are skipped only until its first core0 CSI. Once started,
	// all original pairing/continuity checks apply, including poisoned-session
	// rejection after an error. Finite jobs never skip this prefix.
	void feed(std::size_t receiver, std::string_view session, std::int64_t arrival_us, std::uint16_t port,
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
	std::array<std::size_t, 3> retained_events() const;
	std::array<std::size_t, 3> retained_cells() const;
	// Also readable after a poisoned generation, before its owner discards it.
	WindowDiagnostics diagnostics() const;

private:
	struct Impl;
	std::unique_ptr<Impl> impl_;
};

std::vector<std::uint8_t> encode_piwcsi2(
	const JointWindow& window, std::uint64_t frame_id, std::uint64_t source_time_ns);
std::complex<double> decode_acphy(std::uint32_t word);
} // namespace nexmon_board
