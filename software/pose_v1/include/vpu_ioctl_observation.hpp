#pragma once
#include <filesystem>
#include <memory>
namespace pose::video_observation {
// Observes only linked VPU QBUF/DQBUF calls. Never wraps SDK shared libraries.
class Observer {
public:
    explicit Observer(size_t limit=8192);
    ~Observer();
    Observer(const Observer&)=delete;
    Observer& operator=(const Observer&)=delete;
    void check()const;
    void finish(const std::filesystem::path& freshOutput);
    struct Impl;
private:std::unique_ptr<Impl> p_;
};
}
