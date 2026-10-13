// 显示模块：SDK无关的子进程、IPC和像素处理；传递完整拥有值。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <array>
#include <cstdint>
#include <functional>
#include <cstddef>

namespace pose::display {
    using Cancel = std::function<bool()>;
    constexpr uint32_t nv12Bytes = 1280 * 720 * 3 / 2, poseBytes = (100 + 4200) * sizeof(float);
    struct Pose {
        uint64_t frame = 0, invocation = 0, publishedNs = 0;
        std::array<float, 100> scores {};
        std::array<float, 4200> poses {};
    };
    void validate(const Pose &);
    namespace wire {
        enum class Kind : uint32_t {
            Ready = 1, Render = 2, Image = 3, Stop = 4, Stopped = 5
        };
        struct Header {
            Kind kind;
            uint32_t bytes = 0;
            uint64_t frame = 0, invocation = 0, begin = 0, drawEnd = 0, convertEnd = 0;
        };
        using Bytes = std::array<unsigned char, 64>;
        Bytes encode(const Header &);
        Header decode(const Bytes &);
        uint64_t now();
        // Exact bounded stream operations; one in-flight request gives an explicit credit.
        void write(int fd, const void *, size_t, const Cancel & = {});
        void read(int fd, void *, size_t, const Cancel & = {});
        void writeHeader(int fd, const Header &, const Cancel & = {});
        Header readHeader(int fd, const Cancel & = {}, unsigned idleMs = 5000);
    }

}
