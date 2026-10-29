#pragma once
#include "preprocess.hpp"
#include <array>
#include <cstddef>
#include <cstdint>

namespace pose180_pipeline {
using Tokens = pose_v1::Tokens;
using Window = pose_v1::Window;
constexpr std::size_t candidate_count = 180;
constexpr std::size_t joint_count = 14;
constexpr std::size_t pose_values = candidate_count * joint_count * 3;

// A pool slot owns every byte used by network/archive/display consumers.
// No Tensor, device address, stream view or SDK handle escapes the owner thread.
struct Result {
    std::uint64_t frame_id = 0, source_time_ns = 0, invocation = 0;
    Tokens input{};
    std::array<float, candidate_count> scores{};
    std::array<float, pose_values> poses{};
    std::array<float, joint_count * 3> selected_pose{};
    std::size_t best_index = 0, host_callbacks = 0, zg_callbacks = 0;
    std::uint32_t before_clear = 0, before_forward = 0, completed_layers = 0;
    bool finite_outputs = false;
    double preprocess_ms = 0, prepare_ms = 0, state_clear_ms = 0, forward_ms = 0;
    double final_wait_ms = 0, output_ms = 0, selection_ms = 0, process_ms = 0;
};
static_assert(sizeof(float) == 4, "The FP32 wire/archive contract requires 4-byte floats");
static_assert(sizeof(Tokens) == 43200, "The unchanged input graph requires 10800 FP32 values");
} // namespace pose180_pipeline
