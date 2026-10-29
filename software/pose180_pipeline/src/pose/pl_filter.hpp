#pragma once
#include "fixed_filter.hpp"
#include "fixed_geometry.hpp"
#include "postprocess.hpp"
#include <chrono>
#include <functional>
#include <string>
#include <thread>

namespace pose::post {
class PlFilterError : public std::runtime_error {
public:
	using std::runtime_error::runtime_error;
};

// Caller owns all Device/MMIO access. Never probes r45 or guessed address mappings.
class PlFilter {
	std::function<std::uint32_t(unsigned)> read_;
	std::function<void(unsigned, std::uint32_t)> write_;
	std::uint32_t seq_ = 0;
	bool extended_ = false;
	std::array<std::int32_t, 126> published_{};

public:
	struct Metrics {
		std::uint64_t calls = 0, coordinates = 0, input_ns = 0, wait_ns = 0, output_ns = 0, total_ns = 0,
					  max_ns = 0, compute_cycles = 0, max_cycles = 0;
	};

private:
	Metrics metrics_{};
	Metrics geometry_metrics_{};

public:
	const Metrics& metrics() const {
		return metrics_;
	}

	const Metrics& geometry_metrics() const {
		return geometry_metrics_;
	}

	bool extended() const {
		return extended_;
	}

	void reset_metrics() {
		metrics_ = {};
		geometry_metrics_ = {};
	}

	PlFilter(std::string verified_profile, decltype(read_) read, decltype(write_) write)
		: read_(read), write_(write) {
		extended_ = verified_profile == "probe-free-drain-post-v2";
		if (!extended_ && verified_profile != "pose-stabilizer-offline-v1" &&
			verified_profile != "probe-free-drain-filter-v1")
			throw PlFilterError("PL filter requires explicit new hardware identity");
		if (read_(0) != (extended_ ? 0x504f5302u : 0x504f5301u))
			throw PlFilterError("PL filter ABI mismatch");
	}

	unsigned lanes() const {
		return read_(0x18);
	}

	unsigned cycles() const {
		return read_(0x14);
	}

	std::array<std::int32_t, 126> update(const std::array<std::int32_t, 126>& values, double dt,
		unsigned init_mask, unsigned update_mask = 7) {
		if (!(dt >= .001 && dt <= .25))
			throw PlFilterError("PL filter interval unsupported");
		const auto begin = std::chrono::steady_clock::now();
		const auto p = fixed::parameters(dt);
		if (read_(4) != 0)
			throw PlFilterError("PL filter not idle/healthy");
		write_(0x1c, init_mask);
		write_(0x34, update_mask);
		write_(0x20, p.inverse_dt);
		write_(0x24, p.derivative_alpha);
		write_(0x28, p.k);
		write_(0x2c, p.min_cutoff);
		write_(0x30, p.beta);
		for (unsigned i = 0; i < 126; ++i)
			if (!extended_ || (update_mask & (1u << (i / 42))))
				write_(0x400 + i * 4, std::uint32_t(values[i]));
		write_(0xc, ++seq_);
		write_(8, 1);
		const auto submitted = std::chrono::steady_clock::now();
		auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(2);
		while (read_(0x10) != seq_) {
			if ((read_(4) & 0xf0) || std::chrono::steady_clock::now() >= deadline)
				throw PlFilterError("PL filter isolated; no retry");
		}
		if (read_(4) != 0)
			throw PlFilterError("PL filter completed with error");
		const auto completed = std::chrono::steady_clock::now();
		const auto compute_cycles = cycles();
		for (unsigned i = 0; i < 126; ++i)
			if (!extended_ || (update_mask & (1u << (i / 42))))
				published_[i] = std::int32_t(read_(0x800 + 4 * i));
		const auto end = std::chrono::steady_clock::now();
		auto ns = [](auto elapsed) {
			return std::uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count());
		};
		++metrics_.calls;
		for (unsigned slot = 0; slot < 3; ++slot)
			if (update_mask & (1u << slot))
				metrics_.coordinates += 42;
		metrics_.input_ns += ns(submitted - begin);
		metrics_.wait_ns += ns(completed - submitted);
		metrics_.output_ns += ns(end - completed);
		metrics_.total_ns += ns(end - begin);
		metrics_.max_ns = std::max(metrics_.max_ns, ns(end - begin));
		metrics_.compute_cycles += compute_cycles;
		metrics_.max_cycles = std::max(metrics_.max_cycles, std::uint64_t(compute_cycles));
		return published_;
	}

	GeometrySummary geometry(const std::vector<Person>& people, bool moments) {
		if (!extended_ || people.empty() || people.size() > 3)
			throw PlFilterError("Geometry requires the v2 profile and 1..3 poses");
		const auto begin = std::chrono::steady_clock::now();
		std::array<std::int32_t, 126> values{};
		for (unsigned s = 0; s < people.size(); ++s)
			for (unsigned j = 0; j < 42; ++j) {
				const auto x = people[s].joints[j];
				if (!std::isfinite(x) || std::abs(x) > 16)
					throw PlFilterError("Geometry range unsupported");
				values[s * 42 + j] = fixed::q(x);
			}
		if (read_(4) != 0)
			throw PlFilterError("Geometry not idle/healthy");
		for (unsigned i = 0; i < people.size() * 42; ++i)
			write_(0x400 + 4 * i, std::uint32_t(values[i]));
		write_(0x11c, (1u << people.size()) - 1);
		write_(0x10c, ++seq_);
		write_(0x108, 1);
		const auto submitted = std::chrono::steady_clock::now();
		const auto deadline = submitted + std::chrono::milliseconds(2);
		while (read_(0x110) != seq_) {
			if ((read_(4) & 0xf0) || std::chrono::steady_clock::now() >= deadline)
				throw PlFilterError("Geometry isolated; no retry");
		}
		if (read_(4) != 0)
			throw PlFilterError("Geometry completed with error");
		const auto completed = std::chrono::steady_clock::now();
		const auto cycles = read_(0x114);
		GeometrySummary result;
		result.duplicates = read_(0x118);
		if (moments)
			for (unsigned s = 0; s < people.size(); ++s) {
				for (unsigned a = 0; a < 3; ++a)
					result.centres[s][a] = std::int32_t(read_(0x140 + 4 * (s * 3 + a))) / (14. * 65536.);
				const auto lo = read_(0x140 + 4 * (9 + s * 2)), hi = read_(0x140 + 4 * (10 + s * 2));
				result.radii[s] = std::sqrt(double((std::uint64_t(hi) << 32) | lo)) / (14. * 65536.);
			}
		const auto end = std::chrono::steady_clock::now();
		auto ns = [](auto elapsed) {
			return std::uint64_t(std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count());
		};
		auto& m = geometry_metrics_;
		++m.calls;
		m.coordinates += people.size() * 42;
		m.input_ns += ns(submitted - begin);
		m.wait_ns += ns(completed - submitted);
		m.output_ns += ns(end - completed);
		m.total_ns += ns(end - begin);
		m.max_ns = std::max(m.max_ns, ns(end - begin));
		m.compute_cycles += cycles;
		m.max_cycles = std::max(m.max_cycles, std::uint64_t(cycles));
		return result;
	}
};

// Runs only after the explicit new BOOT/profile was validated. No SDK inference,
// DMA or bus reset; afterwards each live track initializes its own filter slot.
inline unsigned verify_pl_filter(PlFilter& hardware) {
	std::array<fixed::State, 126> state{};
	std::array<std::int32_t, 126> input{};
	unsigned tested = 0;
	for (unsigned f = 0; f < 24; ++f) {
		double dt = f % 3 == 0 ? .067 : f % 3 == 1 ? .11 : .061;
		const auto p = fixed::parameters(dt);
		unsigned mask = f < 2 ? 7 : 1u << (f % 3), init = f == 0 ? 7 : f == 15 ? mask : 0;
		for (unsigned i = 0; i < 126; ++i)
			input[i] = fixed::q(.2 * std::sin(.1 * f + .03 * i) + .002 * i);
		const auto output = hardware.update(input, dt, init, mask);
		for (unsigned i = 0; i < 126; ++i) {
			if (mask & (1u << (i / 42)))
				fixed::step(state[i], input[i], p, (init & (1u << (i / 42))) != 0);
			if (output[i] != state[i].y)
				throw PlFilterError("On-device filter mismatch frame=" + std::to_string(f) +
					" coordinate=" + std::to_string(i) + " actual=" + std::to_string(output[i]) +
					" expected=" + std::to_string(state[i].y));
			++tested;
		}
	}
	return tested;
}

inline unsigned verify_pl_geometry(PlFilter& hardware) {
	if (!hardware.extended())
		return 0;
	unsigned tested = 0;
	for (unsigned f = 0; f < 12; ++f) {
		std::vector<Person> people(f % 3 + 1);
		std::array<std::int32_t, 126> x{};
		for (unsigned s = 0; s < people.size(); ++s)
			for (unsigned j = 0; j < 42; ++j) {
				people[s].joints[j] = float(.2 * std::sin(j * .1 + f * .2) + (j % 3 == 0 ? s * .07 * f : 0));
				x[s * 42 + j] = fixed::q(people[s].joints[j]);
			}
		const auto expected = pose::geometry::evaluate(x, (1u << people.size()) - 1);
		const auto actual = hardware.geometry(people, true);
		if (actual.duplicates != expected.duplicates)
			throw PlFilterError("Geometry self-test mask mismatch");
		for (unsigned s = 0; s < people.size(); ++s) {
			for (unsigned a = 0; a < 3; ++a)
				if (std::abs(actual.centres[s][a] - expected.sums[s][a] / (14. * 65536.)) > 1e-10)
					throw PlFilterError("Geometry self-test centre mismatch");
			if (std::abs(actual.radii[s] - std::sqrt(double(expected.radius[s])) / (14. * 65536.)) > 1e-10)
				throw PlFilterError("Geometry self-test scale mismatch");
		}
		++tested;
	}
	return tested;
}

class PlFilterBackend final : public FilterBackend {
	PlFilter& hardware_;
	std::array<std::uint64_t, 3> tracks_{};
	std::array<std::int32_t, 126> inputs_{};

public:
	explicit PlFilterBackend(PlFilter& hardware) : hardware_(hardware) {
	}

	void reset() override {
		tracks_.fill(0);
		inputs_.fill(0);
	}

	void begin_frame(const std::vector<Person>& ps) override {
		for (auto& id : tracks_)
			if (std::none_of(ps.begin(), ps.end(), [&](const Person& p) {
					return p.track == id;
				}))
				id = 0;
	}

	Joints update(std::uint64_t track, const Joints& x, double dt, bool initialize) override {
		auto it = std::find(tracks_.begin(), tracks_.end(), track);
		if (it == tracks_.end()) {
			it = std::find(tracks_.begin(), tracks_.end(), 0);
			if (it == tracks_.end())
				throw std::runtime_error("PL slots exhausted");
			*it = track;
			initialize = true;
		}
		const unsigned slot = unsigned(it - tracks_.begin());
		for (unsigned i = 0; i < 42; ++i)
			inputs_[slot * 42 + i] = fixed::q(x[i]);
		// Each person may have a different dt after missing frames. Other banks freeze.
		const auto out = hardware_.update(inputs_, dt, initialize ? 1u << slot : 0, 1u << slot);
		Joints result{};
		for (unsigned i = 0; i < 42; ++i)
			result[i] = float(out[slot * 42 + i]) / 65536.f;
		return result;
	}

	std::vector<Joints> update_batch(const std::vector<FilterUpdate>& updates) override {
		if (!hardware_.extended())
			return FilterBackend::update_batch(updates);
		std::vector<Joints> result(updates.size());
		std::vector<unsigned> slots;
		unsigned new_slots = 0;
		for (const auto& u : updates) {
			auto it = std::find(tracks_.begin(), tracks_.end(), u.track);
			if (it == tracks_.end()) {
				it = std::find(tracks_.begin(), tracks_.end(), 0);
				if (it == tracks_.end())
					throw PlFilterError("PL slots exhausted");
				*it = u.track;
				new_slots |= 1u << slots.size();
			}
			const unsigned slot = unsigned(it - tracks_.begin());
			slots.push_back(slot);
			for (unsigned j = 0; j < 42; ++j)
				inputs_[slot * 42 + j] = fixed::q(u.observation[j]);
		}
		unsigned done = 0;
		for (unsigned i = 0; i < updates.size(); ++i)
			if (!(done & (1u << i))) {
				unsigned mask = 0, init = 0, members = 0;
				for (unsigned j = i; j < updates.size(); ++j)
					if (!(done & (1u << j)) && updates[j].dt == updates[i].dt) {
						members |= 1u << j;
						mask |= 1u << slots[j];
						if (updates[j].initialize || (new_slots & (1u << j)))
							init |= 1u << slots[j];
					}
				const auto out = hardware_.update(inputs_, updates[i].dt, init, mask);
				for (unsigned j = i; j < updates.size(); ++j)
					if (members & (1u << j))
						for (unsigned k = 0; k < 42; ++k)
							result[j][k] = float(out[42 * slots[j] + k]) / 65536.f;
				done |= members;
			}
		return result;
	}

	bool geometry(const std::vector<Person>& people, GeometrySummary& result, bool moments) override {
		if (!hardware_.extended())
			return false;
		result = hardware_.geometry(people, moments);
		return true;
	}
};
}
