// 流媒体模块：拥有H264访问单元、有界通道和RTSP；网络对象仅由事件线程操作。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include "online_rtsp.hpp"

namespace pose::stream {
    struct GuardedRtspOptions : RtspOptions {
        unsigned sendBufferBytes = 65536;
        // Per TCP client, no system-wide tuning.
    };
    // Isolated candidate: actual socket buffer bounds and RTP error propagation.
    void serveGuardedAccessUnits(AccessUnitChannel &, const GuardedRtspOptions &, const std::filesystem::path &);
}
