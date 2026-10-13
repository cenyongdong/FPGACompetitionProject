#pragma once
#include "application_core.hpp"
#include <memory>
namespace wifi_demo {
// Owns all required runtime evidence initialization. The caller uses only the
// stable inference interface; diagnostic modules never leak into video/input.
class Engine {
    std::unique_ptr<pose_v1::application::Engine> engine_;
public:
    Engine(const std::filesystem::path& model,const std::filesystem::path& freshEvidence);
    pose_v1::application::Result process_window(const pose_v1::Window& w);
    void save_evidence();
};
}
