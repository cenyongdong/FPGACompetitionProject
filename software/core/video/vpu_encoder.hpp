// 视频模块：有界NV12及V4L2编码；缓冲所有权、正常drain与异常回收保持。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstddef>
#include <filesystem>

namespace pose::video {
    // Fixed validated format720p/NV12, nominal10fps. File-backed finite interface.
    struct EncodeOptions {
        unsigned frameCount = 54;
        // strictly2..60, checked before opening /dev/video0
        bool allowVpuStream = false;
    };
    struct EncodeResult {
        unsigned submitted = 0;
        unsigned returned = 0;
        std::size_t encodedBytes = 0;
        bool drained = false;
    };
    EncodeResult encodeNv12File(const std::filesystem::path& input, const std::filesystem::path& newOutputDirectory, const EncodeOptions& options, bool encode);
}
