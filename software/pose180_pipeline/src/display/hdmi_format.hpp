// SDK无关的固定扫描格式；像素低字节在前。
#pragma once
#include <cstdint>
namespace pose::hdmi {
    constexpr unsigned width = 1920, height = 1080;
    constexpr uint64_t frameBytes = uint64_t(width) * height * 2;
}
