#pragma once
#include <filesystem>
#include <memory>
namespace pose::scratch {
class VpuLoad {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    explicit VpuLoad(const std::filesystem::path& freshEvidence);
    ~VpuLoad();
    void waitReady();
    void check();
    void requestStop(bool abort);
    void join();
};
}
