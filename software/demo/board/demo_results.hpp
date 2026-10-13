// 结果保存：拥有原始窗口和全部模型输出；写入新目录，不覆盖原值。

#pragma once
#include "application_core.hpp"
#include <filesystem>
#include <vector>

namespace wifi_demo {
    class Results {
        struct Row {
            pose_v1::Window input;
            pose_v1::application::Result result;
            uint64_t arrived, returned;
        };
        std::vector<Row > rows_;
        public:
        void add(pose_v1::Window, pose_v1::application::Result, uint64_t arrived, uint64_t returned);
        void save(const std::filesystem::path &) const;
        size_t size() const {
            return rows_.size();
        }

    };
}
