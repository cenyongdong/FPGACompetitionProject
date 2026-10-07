#pragma once
#include <cstddef>
#include <filesystem>

namespace pose::video {
// Fixed validated format720p/NV12, nominal10fps. File-backed finite interface.
struct EncodeOptions {
    unsigned frameCount=54; // strictly2..60, checked before opening /dev/video0
    bool allowVpuStream=false;
};
struct EncodeResult {
    unsigned submitted=0;
    unsigned returned=0;
    std::size_t encodedBytes=0;
    bool drained=false;
};
EncodeResult encodeNv12File(const std::filesystem::path& input,
                           const std::filesystem::path& newOutputDirectory,
                           const EncodeOptions& options, bool encode);
}
