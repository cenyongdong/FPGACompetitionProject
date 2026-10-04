#pragma once
#include <array>
#include <complex>
#include <cstdint>
#include <string>

namespace pose_v1 {
constexpr std::size_t kReceivers = 3, kAntennas = 3, kCarriers = 30, kTimes = 20;
constexpr std::size_t kComplexCount = 3 * 3 * 30 * 20;
constexpr std::size_t kTokenCount = 180 * 60;
constexpr std::size_t kPayloadBytes = kComplexCount * 2 * sizeof(double);
using RawCsi = std::array<std::complex<double>, kComplexCount>;
using Tokens = std::array<float, kTokenCount>;
struct Window {
    std::uint64_t frame_id = 0, source_time_ns = 0;
    RawCsi csi{};
};
constexpr std::size_t raw_index(std::size_t r, std::size_t a, std::size_t n, std::size_t t) {
    return (((r * kAntennas + a) * kCarriers + n) * kTimes + t);
}
// Exact model order: receiver, antenna, time, [30 amplitude, 30 phase].
Tokens preprocess(const RawCsi& csi);
Window read_window(const std::string& filename);
void write_tokens(const std::string& filename, const Tokens& tokens);
}
