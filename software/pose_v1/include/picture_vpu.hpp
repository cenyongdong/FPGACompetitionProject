#pragma once
#include "vpu_pipeline_encoder.hpp"
#include <memory>
namespace pose::picture {
class Vpu {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    Vpu(const std::filesystem::path& fresh,pose::video::OwnedFrame warmup);
    ~Vpu();
    void waitReady();
    void check();
    void publish(pose::video::OwnedFrame);
    void requestStop(bool abort);
    void join();
};
}
