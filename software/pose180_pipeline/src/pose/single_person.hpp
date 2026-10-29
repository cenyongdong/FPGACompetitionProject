#pragma once
#include "geometry.hpp"

namespace pose::post {
// Bounded temporal state for the single-person display. It consumes only the
// actual Top1 observation, never substitutes a lower-ranked query or a score gate.
class SinglePerson {
	Config config_;
	Person accepted_{}, pending_{}, anchor_{};
	geometry::Centre centre_{};
	double radius_ = 0.25;
	unsigned pending_hits_ = 0;
	std::uint64_t pending_first_ = 0;
	std::uint64_t previous_frame_ns_ = 0;
	double frame_dt_ = 0;
	bool active_ = false;
	std::array<OneEuro, 3> centre_filter_;
	std::array<OneEuro, 42> relative_filter_;
	Joints relative_{};
	bool coherent(const Person&, const Person&, double dt) const;
	bool confirm(const Person&, unsigned hits, std::uint64_t span);
	void commit(const Identity&, const Person&, bool initialize, Metrics&);

public:
	explicit SinglePerson(Config c) : config_(c) {
	}

	void reset();
	PresentationFrame update(PresentationFrame, std::uint64_t& next_id, Metrics&);
};
}
