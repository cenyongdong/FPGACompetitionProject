#pragma once
#include <array>
#include <cstddef>
#include <cstdint>
#include <memory>
#include <string>

namespace nexmon_board {

struct Pose180Timings {
    double process_ms = 0;
    double forward_ms = 0;
    double output_wait_ms = 0;
    double readback_ms = 0;
};

struct Pose180Result {
    std::array<float,180> scores{};
    std::array<float,7560> poses{}; // [candidate180, joint14, xyz3]
    std::size_t best_index = 0;
    std::uint64_t invocation = 0;
    Pose180Timings timings{};
};

// Owns one actual SDK Session/Device. No Host compute, sockets or display path.
// The package is the unchanged pose180 deployment package. The evidence output
// directory must be new; every call preserves its input and first output bytes
// before numerical validation. A failed instance never retries inference.
// Calls are sequential; the external runner owns all job/time/frame budgets.
class Pose180Runtime {
public:
    Pose180Runtime(const std::string& package_directory,
                   const std::string& evidence_directory);
    ~Pose180Runtime();
    Pose180Runtime(const Pose180Runtime&) = delete;
    Pose180Runtime& operator=(const Pose180Runtime&) = delete;
    Pose180Runtime(Pose180Runtime&&) = delete;
    Pose180Runtime& operator=(Pose180Runtime&&) = delete;

    Pose180Result infer(const std::array<float,10800>& input);

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace nexmon_board
