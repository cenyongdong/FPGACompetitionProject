// SDK-free adoption/ownership rules. Times are caller-observed steady-clock ns.
#pragma once
#include <cstdint>
#include <stdexcept>

namespace pose::hdmi::detail {
struct AdoptionSample {
	uint32_t status, stopped, address, accepted, faults;
};

class AdoptionState {
	enum class Phase {
		idle,
		reserved,
		waiting,
		failed,
		closed
	};
	Phase phase_ = Phase::idle;
	int current_ = -1, slot_ = -1;
	uint32_t last_id_ = 0, last_address_ = 0, id_ = 0, address_ = 0;
	uint32_t prior_id_ = 0, prior_address_ = 0, prior_stopped_ = 0;
	int64_t begin_ns_ = 0, deadline_ns_ = 0;

	[[noreturn]] void reject(const char* why) {
		phase_ = Phase::failed;
		throw std::runtime_error(why);
	}

public:
	bool pending() const {
		return phase_ == Phase::reserved || phase_ == Phase::waiting || phase_ == Phase::failed;
	}

	bool waiting() const {
		return phase_ == Phase::waiting;
	}

	bool buffers_releasable() const {
		return phase_ == Phase::closed;
	}

	int current_slot() const {
		return current_;
	}

	int target_slot() const {
		return slot_;
	}

	uint32_t target_id() const {
		return id_;
	}

	uint32_t target_address() const {
		return address_;
	}

	int64_t begin_ns() const {
		return begin_ns_;
	}

	int64_t deadline_ns() const {
		return deadline_ns_;
	}

	int next_slot(uint32_t id) const {
		if (phase_ != Phase::idle)
			throw std::runtime_error("HDMI adoption already pending/failed/closed");
		if (!id || id == last_id_)
			throw std::runtime_error("HDMI frame ID invalid/repeated");
		return current_ < 0 ? 0 : 1 - current_;
	}

	void reserve(int slot, uint32_t id, uint32_t address, const AdoptionSample& prior, int64_t begin_ns) {
		if (slot != next_slot(id) || !address || address % 64)
			reject("HDMI target slot/address invalid");
		if (prior.faults || !(prior.status & 0x40) || (prior.status & 0x80000000u))
			reject("HDMI unhealthy before frame write");
		if (current_ >= 0 &&
			(prior.accepted != last_id_ || prior.address != last_address_ || !(prior.status & 2) ||
				(prior.status & 0x91)))
			reject("HDMI accepted buffer changed before next frame");
		slot_ = slot;
		id_ = id;
		address_ = address;
		prior_id_ = prior.accepted;
		prior_address_ = prior.address;
		prior_stopped_ = prior.stopped;
		begin_ns_ = begin_ns;
		deadline_ns_ = 0;
		phase_ = Phase::reserved;
	}

	// Caller must set this immediately after the START/FLIP command returns:
	// duration_cast<nanoseconds>((Clock::now()+200ms).time_since_epoch()).count().
	void wait_after_command(int64_t deadline_ns) {
		if (phase_ != Phase::reserved || deadline_ns <= begin_ns_)
			reject("HDMI adoption deadline anchor invalid");
		deadline_ns_ = deadline_ns;
		phase_ = Phase::waiting;
	}

	bool poll(const AdoptionSample& sample, int64_t observed_ns) {
		if (phase_ == Phase::idle)
			return false;
		if (phase_ != Phase::waiting)
			throw std::runtime_error("HDMI adoption not pollable; STOP required");
		if (sample.faults || !(sample.status & 0x40) || (sample.status & 0x80000000u))
			reject("HDMI fault or PLL lock lost during adoption");
		if (sample.stopped != prior_stopped_ || !(sample.status & 2) || (sample.status & 0x81))
			reject("HDMI stopped while adoption pending");
		// A late observation cannot prove timely adoption. Do not accept a late
		// matching ID/address or extend the fixed deadline after SDK work.
		if (observed_ns >= deadline_ns_)
			reject("HDMI frame adoption deadline");
		const bool target = sample.accepted == id_ && sample.address == address_;
		const bool previous = sample.accepted == prior_id_ && sample.address == prior_address_;
		if (!target && !previous)
			reject("HDMI unexpected accepted frame/address");
		if (!target || (sample.status & 0x10))
			return false;
		current_ = slot_;
		last_id_ = id_;
		last_address_ = address_;
		phase_ = Phase::idle;
		return true;
	}

	void fail() {
		if (phase_ != Phase::closed)
			phase_ = Phase::failed;
	}

	void prove_stop(const AdoptionSample& sample, uint32_t tag) {
		// Fault/PLL state deliberately does not block a valid independent STOP.
		if (!(sample.status & 1) || sample.stopped != tag || (sample.status & 0x3e))
			throw std::runtime_error("HDMI STOP drain not proved; retain frames");
		phase_ = Phase::closed;
	}
};
}
