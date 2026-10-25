#pragma once
#include "types.hpp"
#include <filesystem>
#include <functional>
#include <memory>

namespace icraft::xrt { class Device; }

namespace pose180_pipeline {
struct Config {
    std::filesystem::path graph, raw, evidence;
    // Runs on the same SDK thread after apply. HDMI must allocate on this Device.
    std::function<void(const icraft::xrt::Device&)> on_device_ready;
};

// Construct, infer and destroy on one thread. Exactly one Runtime owns the SDK
// in this process. A failure permanently disables inference; no implicit reset,
// reopening, reread, retry, file deployment or BOOT operation is performed.
class Runtime {
public:
    explicit Runtime(const Config&);
    ~Runtime();
    Runtime(const Runtime&) = delete;
    Runtime& operator=(const Runtime&) = delete;
    Runtime(Runtime&&) = delete;
    Runtime& operator=(Runtime&&) = delete;

    // Writes into an already acquired output pool slot. Normal frames do not
    // create per-frame files. The caller must archive full input/scores/poses
    // before numerical validation, display or recycling this slot.
    // Nonfinite first outputs are preserved and returned with finite_outputs
    // false, while permanently stopping this Runtime, so the archive can finish.
    void infer(const Window&, Result&);
    double init_ms() const;
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
} // namespace pose180_pipeline
