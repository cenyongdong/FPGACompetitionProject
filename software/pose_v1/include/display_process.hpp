#pragma once
#include "display_protocol.hpp"
#include <filesystem>
#include <memory>
#include <vector>

namespace pose::display {
struct Image {
    uint64_t frame=0,invocation=0,renderBegin=0,drawEnd=0,convertEnd=0,receivedEnd=0;
    std::vector<uint8_t> nv12;
};
// One SDK-free executable, one request credit; no inherited SDK context.
// Construct before parent devices/threads; normal STOP/ack and waitpid, no restart.
class Process {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    Process(const std::filesystem::path& executable,const std::filesystem::path& evidence);
    ~Process();
    Process(const Process&)=delete;Process& operator=(const Process&)=delete;
    Image render(const Pose&,const Cancel& = {});
    void finish();
    int pid()const;
};
}
