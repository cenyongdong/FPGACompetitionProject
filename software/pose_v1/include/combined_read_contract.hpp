#pragma once
#include <cstdint>
namespace pose::combined_read {
// 103 windows at 2Hz need 51 seconds after the first accepted record.
constexpr uint64_t readyDurationNs=60000000000ULL;
constexpr unsigned networkSeconds=120;
constexpr unsigned clientSeconds=125;
constexpr unsigned inputFps=2;
constexpr unsigned hardwareSeconds=180;
static_assert(readyDurationNs>102ULL*1000000000ULL/inputFps);
static_assert(networkSeconds+5<hardwareSeconds);
}
