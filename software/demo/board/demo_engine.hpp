// 推理适配：集中配置既有诊断模块，向应用暴露最小推理及保存接口。

#pragma once
#include "application_core.hpp"
#include <memory>

namespace wifi_demo {
    // Owns all required runtime evidence initialization. The caller uses only the
    // stable inference interface; diagnostic modules never leak into video/input.
    class Engine {
        std::unique_ptr<pose_v1::application::Engine > engine_;
        public:
        Engine(const std::filesystem::path& model, const std::filesystem::path& freshEvidence);
        pose_v1::application::Result process_window(const pose_v1::Window& w);
        void save_evidence();
    };
}
