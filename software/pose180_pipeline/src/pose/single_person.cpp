#include "single_person.hpp"
#include <chrono>

namespace pose::post {
using namespace geometry;

void SinglePerson::reset() {
	active_ = false;
	pending_hits_ = 0;
	pending_first_ = previous_frame_ns_ = 0;
	accepted_ = {};
	anchor_ = {};
	for (auto& f : centre_filter_)
		f.reset();
	for (auto& f : relative_filter_)
		f.reset();
}

bool SinglePerson::coherent(const Person& a, const Person& b, double dt) const {
	const auto ac = centre(a.joints), bc = centre(b.joints);
	// Use the previous body's scale: an inflated outlier must not open its gate.
	const double scale = radius(b.joints, bc), interval = std::min(dt, .25);
	if (distance(ac, bc) > scale * (.25 + 3 * interval) ||
		shape(a.joints, ac, b.joints, bc) > scale * (.3 + 2 * interval))
		return false;
	const double maximum = scale * (.65 + 4 * interval);
	for (unsigned j = 0; j < 14; ++j) {
		double sum = 0;
		for (unsigned k = 0; k < 3; ++k) {
			const double d = (a.joints[3 * j + k] - ac[k]) - (b.joints[3 * j + k] - bc[k]);
			sum += d * d;
		}
		if (sum > maximum * maximum)
			return false;
	}
	return true;
}

bool SinglePerson::confirm(const Person& p, unsigned hits, std::uint64_t span) {
	if (!pending_hits_ || p.observed_ns - pending_.observed_ns > 150000000 ||
		!coherent(p, pending_, double(p.observed_ns - pending_.observed_ns) / 1e9)) {
		pending_hits_ = 1;
		pending_first_ = p.observed_ns;
	} else
		++pending_hits_;
	pending_ = p;
	return pending_hits_ >= hits && p.observed_ns - pending_first_ >= span;
}

void SinglePerson::commit(const Identity& id, const Person& p, bool initialize, Metrics& metrics) {
	const auto began = std::chrono::steady_clock::now();
	const auto observation_centre = centre(p.joints);
	const double dt = initialize ? 0 : std::min(.25, double(id.source_ns - accepted_.observed_ns) / 1e9);
	Config centre_config = config_, relative_config = config_;

	// 分别滤波身体中心和相对关节：加强整体位移抑制，避免四肢承担相同延迟。
	centre_config.min_cutoff = std::min(config_.min_cutoff, .35);
	centre_config.beta = std::min(config_.beta, .15);
	relative_config.beta = std::min(config_.beta, .2);
	Centre desired{};
	for (unsigned k = 0; k < 3; ++k)
		desired[k] = centre_filter_[k].update(observation_centre[k], dt, centre_config);
	const double length = distance(desired, centre_);
	const double centre_step = radius_ * (.04 + 1.5 * frame_dt_);
	if (!initialize && length > centre_step) {
		for (unsigned k = 0; k < 3; ++k)
			desired[k] = centre_[k] + (desired[k] - centre_[k]) * centre_step / length;
		++metrics.single_limited;
	}
	for (unsigned k = 0; k < 3; ++k)
		centre_filter_[k].constrain(desired[k]);

	Joints relative{};
	for (unsigned j = 0; j < 42; ++j)
		relative[j] =
			float(relative_filter_[j].update(p.joints[j] - observation_centre[j % 3], dt, relative_config));

	// 所有关节使用同一限幅比例，切换候选时保留相对形状。
	// 限幅后回写滤波器状态，避免内部累积未展示的跳变。
	double maximum = 0;
	for (unsigned j = 0; j < 14; ++j) {
		double sum = 0;
		for (unsigned k = 0; k < 3; ++k)
			sum += std::pow(relative[3 * j + k] - relative_[3 * j + k], 2);
		maximum = std::max(maximum, std::sqrt(sum));
	}
	const double joint_step = radius_ * (.08 + 3 * frame_dt_);
	if (!initialize && maximum > joint_step) {
		for (unsigned j = 0; j < 42; ++j)
			relative[j] = float(relative_[j] + (relative[j] - relative_[j]) * joint_step / maximum);
		++metrics.single_limited;
	}
	const auto offset = centre(relative);
	for (unsigned j = 0; j < 42; ++j) {
		relative[j] -= float(offset[j % 3]);
		relative_filter_[j].constrain(relative[j]);
	}

	const auto track = accepted_.track;
	accepted_ = p;
	accepted_.track = track;
	accepted_.held = false;
	for (unsigned j = 0; j < 42; ++j)
		accepted_.joints[j] = float(desired[j % 3] + relative[j]);
	// The accepted raw observation is kept separately from the displayed body.
	centre_ = desired;
	relative_ = relative;
	const double observed_radius = radius(p.joints, observation_centre);
	radius_ = initialize ? observed_radius
						 : .9 * radius_ + .1 * std::clamp(observed_radius, .5 * radius_, 1.5 * radius_);
	++metrics.cpu_filter_frames;
	metrics.cpu_filter_coordinates += 45;
	const auto elapsed =
		std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now() - began)
			.count();
	metrics.cpu_filter_ns += elapsed;
	metrics.cpu_filter_max_ns = std::max(metrics.cpu_filter_max_ns, std::uint64_t(elapsed));
}

PresentationFrame SinglePerson::update(PresentationFrame out, std::uint64_t& next_id, Metrics& metrics) {
	const auto now = out.id.source_ns;
	// A hidden anchor may survive briefly, but never extends visible validity.
	if (active_ && now - accepted_.observed_ns > 1000000000) {
		reset();
		++metrics.expired;
	}
	frame_dt_ = previous_frame_ns_ ? std::min(.1, double(now - previous_frame_ns_) / 1e9) : 0;
	previous_frame_ns_ = now;
	if (out.raw_poses.empty()) {
		pending_hits_ = 0;
	} else {
		const auto& p = out.raw_poses[0];
		bool accept = false, initialize = false;
		if (!active_) {
			if (confirm(p, config_.confirmation_hits, 90000000)) {
				accepted_.track = next_id++;
				active_ = accept = initialize = true;
				++metrics.births;
				const auto elapsed = now - pending_first_;
				metrics.confirmation_total_ns += elapsed;
				metrics.confirmation_max_ns = std::max(metrics.confirmation_max_ns, elapsed);
			}
		} else if (coherent(p, anchor_, double(now - accepted_.observed_ns) / 1e9)) {
			accept = true;
		} else {
			++metrics.single_rejected;
			if (confirm(p, 4, 180000000)) {
				accept = true;
				++metrics.single_relocations;
			}
		}
		if (accept) {
			commit(out.id, p, initialize, metrics);
			anchor_ = p;
			pending_hits_ = 0;
		}
	}
	if (active_ && now - accepted_.observed_ns <= config_.hold_ns) {
		auto shown = accepted_;
		shown.held = shown.observed_ns != now;
		out.poses.push_back(shown);
	} else if (active_)
		++metrics.hidden_frames;
	return out;
}
}
