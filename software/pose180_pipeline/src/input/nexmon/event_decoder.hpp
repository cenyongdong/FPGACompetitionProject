#pragma once
#include "ingress.hpp"

namespace nexmon_board {
// A real, validated three-antenna event. Time is local to this decoder segment;
// neither it nor the capture wall clock is a shared clock between receivers.
struct CompleteEvent {
	std::uint16_t sequence = 0, frame_control = 0, frame_size = 0;
	std::int64_t local_us = 0, capture_us = 0;
	std::array<std::complex<double>, 3 * 30> csi{}; // antenna, carrier
};

// Shares the original parser, metadata pairing, identity and native-word decode.
// Does not impose a 300 Hz grid. Continuity errors poison only this decoder;
// its owner must replace it before feeding another record.
class EventDecoder {
public:
	EventDecoder(Config config, std::size_t receiver);
	~EventDecoder();
	void feed(std::int64_t capture_us, std::uint16_t port, const std::uint8_t* payload, std::size_t size);
	std::vector<CompleteEvent> take_ready();
	NodeSummary summary() const;

private:
	struct Impl;
	std::unique_ptr<Impl> impl_;
};
} // namespace nexmon_board
