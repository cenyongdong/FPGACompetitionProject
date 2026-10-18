#include "hdmi_canvas.hpp"
#include <algorithm>
#include <stdexcept>

namespace pose::hdmi {
    std::vector<uint8_t> canvas(const std::vector<uint8_t>& source) {
        constexpr unsigned sw = 1280, sh = 720;
        if (source.size() != size_t(sw) * sh * 3) throw std::runtime_error("HDMI canvas requires RGB24 1280x720");
        std::vector<uint8_t> result(frameBytes);
        for (unsigned y = 0; y < height; ++y) {
            // 像素中心对齐，坐标采用1/6像素单位，固定3/2比例无需浮点。
            const int sy6 = std::clamp(int(4 * y) - 1, 0, int(6 * (sh - 1)));
            const unsigned y0 = unsigned(sy6 / 6), y1 = std::min(y0 + 1, sh - 1), fy = unsigned(sy6 % 6);
            for (unsigned x = 0; x < width; ++x) {
                const int sx6 = std::clamp(int(4 * x) - 1, 0, int(6 * (sw - 1)));
                const unsigned x0 = unsigned(sx6 / 6), x1 = std::min(x0 + 1, sw - 1), fx = unsigned(sx6 % 6);
                unsigned channels[3];
                for (unsigned c = 0; c < 3; ++c) {
                    const auto a = source[(size_t(y0) * sw + x0) * 3 + c];
                    const auto b = source[(size_t(y0) * sw + x1) * 3 + c];
                    const auto d = source[(size_t(y1) * sw + x0) * 3 + c];
                    const auto e = source[(size_t(y1) * sw + x1) * 3 + c];
                    channels[c] = ((a * (6 - fx) + b * fx) * (6 - fy) +
                                   (d * (6 - fx) + e * fx) * fy + 18) / 36;
                }
                const uint16_t pixel = uint16_t(((channels[0] >> 3) << 11) |
                                                ((channels[1] >> 2) << 5) | (channels[2] >> 3));
                const size_t at = (size_t(y) * width + x) * 2;
                result[at] = uint8_t(pixel); result[at + 1] = uint8_t(pixel >> 8);
            }
        }
        return result;
    }
}
