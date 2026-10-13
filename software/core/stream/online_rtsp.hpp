// 流媒体模块：拥有H264访问单元、有界通道和RTSP；网络对象仅由事件线程操作。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include "access_unit_channel.hpp"
#include <filesystem>

namespace pose::stream {
    struct RtspOptions {
        unsigned port = 8554, maximumSeconds = 90, maximumClients = 2;
    };
    // Runs synchronously on one dedicated network thread. Caller owns the producer
    // and must join it before destroying the channel. Fresh output directory only.
    void serveOwnedAccessUnits(AccessUnitChannel &, const RtspOptions &, const std::filesystem::path& freshResults);
}
