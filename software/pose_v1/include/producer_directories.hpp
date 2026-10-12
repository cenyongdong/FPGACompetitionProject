#pragma once
#include <filesystem>
#include <thread>
#include <vector>
#include <cstdint>

namespace pose::producer_directories {
// Exclusive evidence root; no deletion/reuse. All filesystem operations are
// confined to construction, prepare and saveSummary, never consume.
class PreparedDirectories final {
public:
    explicit PreparedDirectories(const std::filesystem::path& freshRoot);
    PreparedDirectories(const PreparedDirectories&) = delete;
    PreparedDirectories& operator=(const PreparedDirectories&) = delete;
    void prepare(unsigned count);
    std::filesystem::path consume(unsigned invocation);
    void saveSummary() const;
private:
    void owner() const;
    std::filesystem::path root_;
    std::thread::id owner_;
    std::vector<std::filesystem::path> paths_;
    unsigned consumed_ = 0;
    bool attempted_ = false, prepared_ = false;
    uint64_t begin_ = 0, end_ = 0;
};
}
