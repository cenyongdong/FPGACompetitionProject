#pragma once
#include "types.hpp"
#include <algorithm>
#include <array>
#include <cmath>
#include <cstring>
#include <stdexcept>

namespace pose180_pipeline {
constexpr std::size_t input_bytes = 86432, full_bytes = 74544;

inline void put64(unsigned char* p, std::uint64_t n) {
	for (unsigned i = 0; i < 8; ++i)
		p[i] = static_cast<unsigned char>(n >> (8 * i));
}

inline void put32(unsigned char* p, std::uint32_t n) {
	for (unsigned i = 0; i < 4; ++i)
		p[i] = static_cast<unsigned char>(n >> (8 * i));
}

inline std::uint64_t get64(const unsigned char* p) {
	std::uint64_t n = 0;
	for (unsigned i = 0; i < 8; ++i)
		n |= std::uint64_t(p[i]) << (8 * i);
	return n;
}

inline std::uint32_t get32(const unsigned char* p) {
	return static_cast<std::uint32_t>(get64(p) & 0xffffffffu);
}

inline void decode_input(const std::array<unsigned char, input_bytes>& bytes, Window& window) {
	if (std::memcmp(bytes.data(), "PIWCSI2\0", 8) || get32(bytes.data() + 8) != 2 ||
		get32(bytes.data() + 12) != 86400)
		throw std::runtime_error("Invalid complete simulated CSI record");
	window.frame_id = get64(bytes.data() + 16);
	window.source_time_ns = get64(bytes.data() + 24);
	for (std::size_t r = 0; r < 3; ++r)
		for (std::size_t a = 0; a < 3; ++a)
			for (std::size_t t = 0; t < 20; ++t)
				for (std::size_t n = 0; n < 30; ++n) {
					auto off = 32 + (((r * 3 + a) * 20 + t) * 30 + n) * 16;
					double re, im;
					std::memcpy(&re, bytes.data() + off, 8);
					std::memcpy(&im, bytes.data() + off + 8, 8);
					if (!std::isfinite(re) || !std::isfinite(im))
						throw std::runtime_error("Non-finite simulated input");
					window.csi[pose_v1::raw_index(r, a, n, t)] = {re, im};
				}
}

// Archive encoding intentionally preserves all first values, including invalid
// floats. Validation belongs AFTER the complete Host archive ACK.
inline void encode_full(std::array<unsigned char, full_bytes>& bytes, const Result& r, std::uint64_t session,
	std::uint64_t sequence, std::uint64_t arrived, std::uint64_t began, std::uint64_t returned,
	std::uint64_t published, std::uint32_t depth) {
	bytes.fill(0);
	std::memcpy(bytes.data(), "PIWFUL3\0", 8);
	put32(bytes.data() + 8, 3);
	put32(bytes.data() + 12, full_bytes);
	const std::uint64_t fields[] = {
		session, r.frame_id, r.invocation, r.source_time_ns, arrived, began, returned, sequence};
	for (unsigned i = 0; i < 8; ++i)
		put64(bytes.data() + 16 + 8 * i, fields[i]);
	const double timing[] = {r.process_ms, r.preprocess_ms, r.forward_ms, r.output_ms};
	std::memcpy(bytes.data() + 80, timing, sizeof(timing));
	put32(bytes.data() + 112, depth);
	put32(bytes.data() + 116, 180);
	put32(bytes.data() + 120, static_cast<std::uint32_t>(r.best_index));
	auto p = bytes.data() + 128;
	std::memcpy(p, "PIWPOSE1", 8);
	p[8] = 1;
	p[10] = 88;
	put32(p + 12, 256);
	const std::uint64_t pose_fields[] = {session, r.frame_id, r.invocation, r.source_time_ns, published};
	for (unsigned i = 0; i < 5; ++i)
		put64(p + 16 + i * 8, pose_fields[i]);
	put32(p + 56, static_cast<std::uint32_t>(r.best_index));
	p[60] = 14;
	float score = r.best_index < r.scores.size() ? r.scores[r.best_index] : 0;
	std::memcpy(p + 64, &score, 4);
	put32(p + 68, 1);
	put32(p + 72, 1);
	put64(p + 80, sequence);
	std::memcpy(p + 88, r.selected_pose.data(), 168);
	p += 256;
	std::memcpy(p, r.input.data(), sizeof(r.input));
	p += sizeof(r.input);
	std::memcpy(p, r.scores.data(), sizeof(r.scores));
	p += sizeof(r.scores);
	std::memcpy(p, r.poses.data(), sizeof(r.poses));
}
}
