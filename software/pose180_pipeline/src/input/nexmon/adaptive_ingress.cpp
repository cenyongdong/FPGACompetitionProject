#include "adaptive_ingress.hpp"
#include <algorithm>
#include <cmath>
#include <deque>
#include <limits>
#include <optional>

namespace nexmon_board {
namespace {
void require(bool v, const char* why) {
	if (!v)
		throw std::runtime_error(why);
}

constexpr auto unset = std::numeric_limits<std::int64_t>::min();

struct Sample {
	CompleteEvent event;
	std::int64_t sequence = 0, seen_us = 0;
	std::uint32_t index = 0;
};

struct Anchor {
	double x = 0, y = 0;
};

struct Model {
	bool valid = false;
	double x = 0, y = 0, slope = 1, residual = 0;
	std::int64_t tolerance = 0, seen_us = 0;

	double map(double local) const {
		return y + (local - x) * slope;
	}
};

double quantile(std::vector<double> v, double p) {
	if (v.empty())
		return 0;
	std::sort(v.begin(), v.end());
	return v[std::min(v.size() - 1, std::size_t(std::ceil(p * double(v.size()))) - 1)];
}

// Centred least squares, followed by one robust residual trim. No CSI values
// are changed. Fitting uses ONLY exact common wireless events, never a model's
// own nearest-neighbour matches, so degraded output cannot validate itself.
Model fit(const std::deque<Anchor>& history, double spacing, std::int64_t cap, std::int64_t seen) {
	Model m;
	if (history.size() < 32)
		return m;
	std::vector<Anchor> points(history.begin(), history.end());
	if (points.back().x - points.front().x < 100000)
		return m;
	auto regress = [&]() {
		m.x = m.y = 0;
		for (const auto& a : points) {
			m.x += a.x;
			m.y += a.y;
		}
		m.x /= double(points.size());
		m.y /= double(points.size());
		double xx = 0, xy = 0;
		for (const auto& a : points) {
			xx += (a.x - m.x) * (a.x - m.x);
			xy += (a.x - m.x) * (a.y - m.y);
		}
		m.slope = xx > 0 ? xy / xx : 0;
	};
	regress();
	std::vector<double> residuals;
	for (const auto& a : points)
		residuals.push_back(std::abs(a.y - m.map(a.x)));
	const auto trim = std::max(200.0, 4 * quantile(residuals, .5));
	points.erase(std::remove_if(points.begin(), points.end(),
					 [&](const Anchor& a) {
						 return std::abs(a.y - m.map(a.x)) > trim;
					 }),
		points.end());
	if (points.size() < 32 || points.size() * 5 < history.size() * 4)
		return Model{};
	regress();
	residuals.clear();
	for (const auto& a : history)
		residuals.push_back(std::abs(a.y - m.map(a.x)));
	m.residual = quantile(residuals, .95);
	m.valid = std::isfinite(m.slope) && m.slope >= .995 && m.slope <= 1.005 && m.residual <= 833.333;
	// One observed sampling interval plus cross-RX mapping uncertainty. The
	// independent sequence bound remains in force even when spacing is noisy.
	m.tolerance = std::clamp(std::int64_t(std::ceil(spacing + 2 * m.residual)), std::int64_t(833), cap);
	m.seen_us = seen;
	return m;
}

std::int64_t near_sequence(std::uint16_t seq, std::int64_t reference) {
	const auto raw = std::int64_t(seq >> 4);
	auto delta = (raw - (reference & 4095) + 4096) & 4095;
	if (delta >= 2048)
		delta -= 4096;
	return reference + delta;
}
}

struct AdaptiveIngress::Impl {
	AdaptiveConfig config;
	std::array<std::unique_ptr<EventDecoder>, 3> decoders;
	std::array<std::deque<Sample>, 3> queues;
	std::array<std::deque<Anchor>, 3> anchors;
	std::array<Model, 3> active{}, pending{};
	std::array<std::int64_t, 3> last_used{unset, unset, unset};
	std::array<std::uint32_t, 3> next_index{};
	std::deque<double> spacings;
	std::deque<AdaptiveWindow> ready;
	AdaptiveWindow partial;
	AdaptiveDiagnostics diagnostic;
	std::int64_t reference = unset, last_anchor = unset, last_decided = unset, now = 0;
	std::int64_t first_local = 0, partial_seen = 0, previous_local = unset;
	std::size_t points = 0, new_anchors = 0;
	bool pending_ready = false, poisoned = false;

	explicit Impl(AdaptiveConfig c) : config(std::move(c)) {
		require(config.source.streaming, "Adaptive CSI is streaming-only; strict finite mode is unchanged");
		require(config.max_skew_us >= 833 && config.max_skew_us <= 10000,
			"Adaptive skew cap must be 833..10000 us");
		require(config.max_sequence_skew <= 3, "Adaptive sequence cap must be 0..3 samples");
		require(config.max_wait_us >= 0 && config.max_wait_us <= 30000, "Adaptive wait must be bounded");
		require(config.max_age_us >= 20000 && config.max_age_us <= 500000, "Adaptive age must be bounded");
		require(config.max_window_span_us >= 66666 && config.max_window_span_us <= 150000,
			"Adaptive window span must be bounded");
		for (std::size_t r = 0; r < 3; ++r)
			decoders[r] = std::make_unique<EventDecoder>(config.source, r);
	}

	void discard_partial() {
		if (points)
			++diagnostic.expired_windows;
		points = 0;
		partial = {};
	}

	void reset_decoder(std::size_t r, const ContinuityDiagnostic& d) {
		diagnostic.last_continuity = d;
		++diagnostic.decoder_resets[r];
		decoders[r] = std::make_unique<EventDecoder>(config.source, r);
		queues[r].clear();
		// Decoder-local time has changed origin. Keep healthy TCP/parser state,
		// but never reuse that segment's affine model or a half-built window.
		discard_partial();
		pending_ready = false;
		pending = {};
		new_anchors = 0;
		last_anchor = unset;
		if (r == 0) {
			active = {};
			for (auto& a : anchors)
				a.clear();
			previous_local = unset;
			spacings.clear();
		} else {
			active[r] = {};
			anchors[r].clear();
		}
	}

	const Sample* exact(std::size_t r, std::int64_t sequence) const {
		const auto& q = queues[r];
		const auto it = std::lower_bound(q.begin(), q.end(), sequence, [](const Sample& s, std::int64_t n) {
			return s.sequence < n;
		});
		return it != q.end() && it->sequence == sequence ? &*it : nullptr;
	}

	void learn(const Sample& ref) {
		if (ref.sequence <= last_anchor && last_anchor != unset)
			return;
		const auto* b = exact(1, ref.sequence);
		const auto* c = exact(2, ref.sequence);
		if (!b || !c || b->event.frame_size != ref.event.frame_size ||
			c->event.frame_size != ref.event.frame_size)
			return;
		for (std::size_t r = 1; r < 3; ++r) {
			const auto* e = r == 1 ? b : c;
			anchors[r].push_back({double(e->event.local_us), double(ref.event.local_us)});
			if (anchors[r].size() > 120)
				anchors[r].pop_front();
		}
		last_anchor = ref.sequence;
		if (++new_anchors < 20)
			return;
		new_anchors = 0;
		std::vector<double> gaps(spacings.begin(), spacings.end());
		const auto spacing = gaps.empty() ? 3333.333 : quantile(gaps, .95);
		auto candidate = active;
		for (std::size_t r = 1; r < 3; ++r)
			candidate[r] = fit(anchors[r], spacing, config.max_skew_us, now);
		if (candidate[1].valid && candidate[2].valid) {
			pending = candidate;
			pending_ready = true;
			++diagnostic.shadow_fits;
		} else
			++diagnostic.shadow_rejected;
	}

	void boundary() {
		if (points || !pending_ready)
			return;
		active = pending;
		pending_ready = false;
		++diagnostic.alignment_version;
		++diagnostic.switches;
	}

	const Sample* choose(std::size_t r, const Sample& ref, double& skew) const {
		skew = 0;
		if (ref.sequence <= last_used[r])
			return nullptr;
		const auto* same = exact(r, ref.sequence);
		if (same && same->sequence > last_used[r] && now - same->seen_us <= config.max_age_us &&
			same->event.frame_size == ref.event.frame_size)
			return same;
		// A previous fallback may have consumed this reference's exact event.
		// Skip this reference once to rejoin exact matching; do not chase one
		// future event forever after a single missing sample.
		if (same && same->sequence <= last_used[r])
			return nullptr;
		const auto& m = active[r];
		if (!m.valid || now - m.seen_us > 2000000)
			return nullptr;
		const Sample* best = nullptr;
		double error = std::numeric_limits<double>::infinity();
		for (const auto& s : queues[r]) {
			if (s.sequence <= last_used[r] || now - s.seen_us > config.max_age_us ||
				s.event.frame_size != ref.event.frame_size ||
				std::abs(s.sequence - ref.sequence) > config.max_sequence_skew)
				continue;
			const auto delta = std::abs(m.map(double(s.event.local_us)) - double(ref.event.local_us));
			if (delta <= m.tolerance && delta < error) {
				best = &s;
				error = delta;
			}
		}
		if (best)
			skew = error;
		return best;
	}

	void pump() {
		if (points && now - partial_seen > config.max_age_us)
			discard_partial();
		auto& q = queues[0];
		while (!q.empty()) {
			const auto& ref = q.front();
			if (ref.sequence <= last_decided && last_decided != unset) {
				q.pop_front();
				continue;
			}
			const bool all_exact = exact(1, ref.sequence) && exact(2, ref.sequence);
			// Wait briefly for the same wireless event before considering a
			// neighbouring event. Neither wait nor shadow fitting blocks SDK.
			if (!all_exact && now - ref.seen_us < config.max_wait_us)
				break;
			learn(ref);
			boundary();
			if (now - ref.seen_us > config.max_age_us) {
				last_decided = ref.sequence;
				++diagnostic.skipped_points;
				q.pop_front();
				continue;
			}
			double b_skew = 0, c_skew = 0;
			const auto* b = choose(1, ref, b_skew);
			const auto* c = choose(2, ref, c_skew);
			if (!b || !c) {
				last_decided = ref.sequence;
				++diagnostic.skipped_points;
				q.pop_front();
				continue;
			}
			if (points &&
				(ref.event.local_us < first_local ||
					ref.event.local_us - first_local > config.max_window_span_us)) {
				discard_partial();
				boundary();
				// The pair was chosen with the old model; retry under the new
				// model so even this exceptional boundary cannot mix versions.
				continue;
			}
			if (!points) {
				first_local = ref.event.local_us;
				partial_seen = ref.seen_us;
				partial.alignment_version = diagnostic.alignment_version;
				for (std::size_t r = 1; r < 3; ++r)
					partial.tolerance_us[r] = active[r].tolerance;
			}
			const std::array<const Sample*, 3> selected{&ref, b, c};
			for (std::size_t r = 0; r < 3; ++r) {
				const auto& s = *selected[r];
				last_used[r] = s.sequence;
				partial.sequences[r][points] = s.sequence;
				partial.window.event_indices[r][points] = s.index;
				for (std::size_t a = 0; a < 3; ++a)
					for (std::size_t n = 0; n < 30; ++n)
						partial.window.csi[((r * 3 + a) * 20 + points) * 30 + n] = s.event.csi[a * 30 + n];
			}
			if (b->sequence != ref.sequence || c->sequence != ref.sequence)
				++partial.approximate_points;
			partial.max_skew_us =
				std::max(partial.max_skew_us, std::int64_t(std::ceil(std::max(b_skew, c_skew))));
			partial.span_us = ref.event.local_us - first_local;
			partial.window.source_time_ns = std::uint64_t(ref.event.capture_us) * 1000;
			last_decided = ref.sequence;
			if (++points == 20) {
				partial.window.start_reference_slot = partial.sequences[0][0];
				if (partial.approximate_points)
					++diagnostic.approximate_windows;
				else
					++diagnostic.exact_windows;
				diagnostic.approximate_points += partial.approximate_points;
				if (ready.size() == 4) {
					ready.pop_front();
					++diagnostic.ready_dropped;
				}
				ready.push_back(std::move(partial));
				partial = {};
				points = 0;
			}
			q.pop_front();
			for (std::size_t r = 1; r < 3; ++r) {
				auto& peer = queues[r];
				while (!peer.empty() &&
					(peer.front().sequence <= last_used[r] || now - peer.front().seen_us > config.max_age_us))
					peer.pop_front();
			}
		}
	}

	void accept(std::size_t r, CompleteEvent event) {
		if (r == 0) {
			if (reference == unset)
				reference = event.sequence >> 4;
			else {
				const auto next = near_sequence(event.sequence, reference);
				if (next <= reference)
					return; // old/repeated identity after recovery
				reference = next;
			}
			if (previous_local != unset && event.local_us > previous_local) {
				const auto delta = event.local_us - previous_local;
				if (delta < 10000) {
					spacings.push_back(double(delta));
					if (spacings.size() > 120)
						spacings.pop_front();
				}
			}
			previous_local = event.local_us;
			// Before RX1's first event, other receivers may already have data.
			for (std::size_t peer = 1; peer < 3; ++peer)
				for (auto& s : queues[peer])
					if (s.index == std::numeric_limits<std::uint32_t>::max()) {
						s.sequence = near_sequence(s.event.sequence, reference);
						s.index = next_index[peer]++;
					}
		}
		Sample sample;
		sample.event = std::move(event);
		sample.seen_us = now;
		sample.sequence = reference == unset
			? (queues[r].empty() ? sample.event.sequence >> 4
								 : near_sequence(sample.event.sequence, queues[r].back().sequence))
			: near_sequence(sample.event.sequence, reference);
		sample.index = reference == unset ? std::numeric_limits<std::uint32_t>::max() : next_index[r]++;
		if (reference != unset && std::abs(sample.sequence - reference) > 256)
			return;
		auto& q = queues[r];
		if (!q.empty() && sample.sequence <= q.back().sequence)
			return;
		q.push_back(std::move(sample));
		if (q.size() > 256)
			q.pop_front();
		if (reference != unset)
			pump();
	}
};

AdaptiveIngress::AdaptiveIngress(AdaptiveConfig c) : impl_(std::make_unique<Impl>(std::move(c))) {
}

AdaptiveIngress::~AdaptiveIngress() = default;

void AdaptiveIngress::feed(std::size_t r, std::string_view session, std::int64_t capture, std::uint16_t port,
	const std::uint8_t* p, std::size_t size, std::int64_t observed) {
	auto& i = *impl_;
	require(
		!i.poisoned && r < 3 && session == i.config.source.session_id, "Adaptive source/session rejected");
	require(observed >= i.now, "Adaptive observation clock moved backwards");
	i.now = observed;
	try {
		try {
			i.decoders[r]->feed(capture, port, p, size);
		} catch (const ContinuityError& e) {
			i.reset_decoder(r, e.diagnostic());
			i.pump();
			return;
		}
		for (auto& event : i.decoders[r]->take_ready())
			i.accept(r, std::move(event));
	} catch (...) {
		i.poisoned = true;
		throw;
	}
}

void AdaptiveIngress::poll(std::int64_t observed) {
	auto& i = *impl_;
	require(!i.poisoned && observed >= i.now, "Adaptive poll clock/session rejected");
	i.now = observed;
	i.pump();
}

std::vector<AdaptiveWindow> AdaptiveIngress::take_ready() {
	require(!impl_->poisoned, "Adaptive source rejected");
	std::vector<AdaptiveWindow> out;
	while (!impl_->ready.empty()) {
		out.push_back(std::move(impl_->ready.front()));
		impl_->ready.pop_front();
	}
	return out;
}

AdaptiveDiagnostics AdaptiveIngress::diagnostics() const {
	auto d = impl_->diagnostic;
	d.partial_points = std::uint32_t(impl_->points);
	for (std::size_t r = 0; r < 3; ++r) {
		d.nodes[r] = impl_->decoders[r]->summary();
		d.queued_events[r] = impl_->queues[r].size();
		d.tolerance_us[r] = impl_->active[r].tolerance;
	}
	return d;
}
} // namespace nexmon_board
