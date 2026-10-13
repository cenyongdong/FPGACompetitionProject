// 视频编排：绘图、VPU及网络分别拥有工作线程；finish后全部join。

#pragma once
#include "display_process.hpp"
#include <filesystem>
#include <memory>

namespace wifi_demo {
    // Owns display/encoder/network workers; the caller retains the SDK-free child
    // and the main-thread inference engine until finish has joined every worker.
    class Video {
        public:
        Video(pose::display::Process &, const std::filesystem::path &, unsigned rtspPort);
        ~Video();
        Video(const Video &) = delete;
        Video& operator = (const Video &) = delete;
        void waitCapture();
        void beginInitialization();
        void initialized();
        void publish(pose::display::Pose);
        void check();
        void abort(std::exception_ptr);
        void finish();
        private:
        struct Impl;
        std::unique_ptr<Impl > p_;
    };
}
