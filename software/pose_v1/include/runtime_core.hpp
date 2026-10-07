#pragma once
#include "preprocess.hpp"
#include <array>
#include <filesystem>
#include <memory>
#include <string>

namespace pose_v1::runtime {
struct Config {
    std::filesystem::path graph, raw, evidence;
    bool allow_device_init=false, capture=false, minimal_log=false;
};
struct Result {
    uint64_t frame_id=0, source_time_ns=0, invocation=0;
    Tokens input{};
    std::string scores, poses;
    std::array<float,42> selected_pose{};
    size_t best_index=0, host_callbacks=0, zg_callbacks=0;
    uint32_t before_clear=0, before_forward=0, completed_layers=0;
    double preprocess_ms=0, prepare_ms=0, state_clear_ms=0, forward_ms=0;
    double final_wait_ms=0, output_ms=0, selection_ms=0, process_ms=0, cpu_ms=0;
};
// Exactly one engine per process; no concurrent calls. Exceptions permanently
// stop this engine. Destruction never resets/reopens the hardware.
class Engine {
public:
    explicit Engine(const Config& config);
    ~Engine();
    Engine(const Engine&)=delete;
    Engine& operator=(const Engine&)=delete;
    Result process_window(const Window&, const std::string& case_name,
                          const Tokens& expected_input);
    void save_evidence(); // Outside measured processing; does not access/reset hardware.
    double init_ms() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
