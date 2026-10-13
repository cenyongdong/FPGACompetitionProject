// 推理适配：集中配置既有诊断模块，向应用暴露最小推理及保存接口。

#include "demo_engine.hpp"
#include "host_failure_evidence.hpp"
#include "failure_source_readback.hpp"
#include "host_stage_observation.hpp"
#include "producer_count_observation.hpp"
#include "tensor_identity_observation.hpp"
#include <functional>

namespace wifi_demo {
    Engine::Engine(const std::filesystem::path& model, const std::filesystem::path& out) {
        if (!std::filesystem::create_directory(out)) throw std::runtime_error("Fresh Engine evidence directory required");
        const auto parent = out.parent_path();
        pose::failure_evidence::configure(parent / "failed-host-inputs");
        pose::source_diagnostic::configure(parent / "failed-host-inputs/source-readback");
        pose::stage_observation::configure(parent / "copy-observations");
        pose::producer_count::configure(parent / "producer-counts");
        pose::tensor_identity::configure(parent / "tensor-identities");
        pose_v1::application::Config cfg;
        cfg.graph = model / "piw24_ZG.json";
        cfg.raw = model / "piw24_ZG.raw";
        cfg.evidence = out;
        cfg.allow_device_init = true;
        cfg.minimal_log = true;
        cfg.diagnostic_frames = 0;
        cfg.timing_frames = 0;
        engine_ = std::make_unique<pose_v1::application::Engine>(cfg);
    }

    pose_v1::application::Result Engine::process_window(const pose_v1::Window& w) {
        return engine_->process_window(w);
    }

    void Engine::save_evidence() {
        std::exception_ptr first;
        const std::function<void() > tasks[] = {
            [&] {
                engine_->save_evidence();
            }, [] {
                pose::stage_observation::saveMetadata();
            }, [] {
                pose::producer_count::save();
            }, [] {
                pose::tensor_identity::save();
            }
        };
        for (const auto & task : tasks) {
            try {
                task();
            } catch (...) {
                if (!first) first = std::current_exception();
            }
        }

        if (first) std::rethrow_exception(first);
    }

}
