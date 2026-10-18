// SDK无关的显示格式适配；不改变模型输出、候选选择或投影算法。
#pragma once
#include "hdmi_format.hpp"
#include <vector>
namespace pose::hdmi {
    // 固定1280×720 RGB24拥有值→1920×1080 RGB565LE拥有值；双线性缩放。
    std::vector<uint8_t> canvas(const std::vector<uint8_t>& rgb720);
}
