// Drawing primitives for tightly packed RGB565, low byte first.
#pragma once
#include "font5x7.hpp"
#include "hdmi_format.hpp"
#include <algorithm>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace pose::hdmi::detail {
    // Full-width scene below the compact status header, matching the PC view.
    constexpr int left = 0, right = 1919, top = 250, bottom = 1039;
    constexpr size_t frame_bytes = size_t(pose::hdmi::frameBytes);

    constexpr uint16_t color(unsigned r, unsigned g, unsigned b) {
        return uint16_t(((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3));
    }

    inline void pixel(std::vector<uint8_t>& image, int x, int y, uint16_t value) {
        if (x < 0 || x >= width || y < 0 || y >= height) return;
        const auto offset = (size_t(y) * width + unsigned(x)) * 2;
        image[offset] = uint8_t(value);
        image[offset + 1] = uint8_t(value >> 8);
    }

    inline void rect(std::vector<uint8_t>& image, int x0, int y0, int x1, int y1, uint16_t value) {
        x0 = std::max(x0, 0); x1 = std::min(x1, int(width));
        y0 = std::max(y0, 0); y1 = std::min(y1, int(height));
        if (x0 >= x1 || y0 >= y1) return;
        for (int y = y0; y < y1; ++y) {
            auto* row = image.data() + (size_t(y) * width + unsigned(x0)) * 2;
            for (int x = x0; x < x1; ++x) {
                *row++ = uint8_t(value);
                *row++ = uint8_t(value >> 8);
            }
        }
    }

    inline int code(double x, double y) {
        return (x < left ? 1 : 0) | (x > right ? 2 : 0) |
               (y < top ? 4 : 0) | (y > bottom ? 8 : 0);
    }

    inline bool clip(double& x0, double& y0, double& x1, double& y1) {
        for (int step = 0; step < 8; ++step) {
            const int a = code(x0, y0), b = code(x1, y1);
            if (!(a | b)) return true;
            if (a & b) return false;
            const int c = a ? a : b;
            double x = 0, y = 0;
            if (c & 8) {
                y = bottom; x = x0 + (x1 - x0) * (bottom - y0) / (y1 - y0);
            } else if (c & 4) {
                y = top; x = x0 + (x1 - x0) * (top - y0) / (y1 - y0);
            } else if (c & 2) {
                x = right; y = y0 + (y1 - y0) * (right - x0) / (x1 - x0);
            } else {
                x = left; y = y0 + (y1 - y0) * (left - x0) / (x1 - x0);
            }
            if (!std::isfinite(x) || !std::isfinite(y))
                throw std::runtime_error("Projection clipping failed");
            if (c == a) { x0 = x; y0 = y; }
            else { x1 = x; y1 = y; }
        }
        throw std::runtime_error("Clipping did not converge");
    }

    inline void line(std::vector<uint8_t>& image, double a, double b, double c, double d,
                     uint16_t value, double thickness = 1.5) {
        if (!clip(a, b, c, d)) return;
        int x0 = int(std::lround(a)), y0 = int(std::lround(b));
        const int x1 = int(std::lround(c)), y1 = int(std::lround(d));
        // Keep the fractional phase when rasterizing a nominal 4.5px stroke;
        // integer rectangles occupy four or five pixels, without a 6/7px stamp.
        const double phase_x = a - x0, phase_y = b - y0;
        const int dx = std::abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
        const int dy = -std::abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
        int error = dx + dy;
        for (;;) {
            rect(image, int(std::floor(x0 + phase_x - thickness / 2)),
                 int(std::floor(y0 + phase_y - thickness / 2)),
                 int(std::floor(x0 + phase_x + thickness / 2)),
                 int(std::floor(y0 + phase_y + thickness / 2)), value);
            if (x0 == x1 && y0 == y1) break;
            const int twice = 2 * error;
            if (twice >= dy) { error += dy; x0 += sx; }
            if (twice <= dx) { error += dx; y0 += sy; }
        }
    }

    inline void text(std::vector<uint8_t>& image, double x, double y,
                     const std::string& value, double scale, uint16_t ink) {
        for (const char c : value) {
            const Glyph* glyph = nullptr;
            for (const auto& candidate : glyphs)
                if (candidate.code == c) { glyph = &candidate; break; }
            if (!glyph) throw std::runtime_error("Unsupported render glyph");
            for (int row = 0; row < 7; ++row)
                for (int col = 0; col < 5; ++col)
                    if (glyph->rows[row] & (1 << (4 - col)))
                        rect(image, int(std::floor(x + col * scale)),
                             int(std::floor(y + row * scale)),
                             int(std::floor(x + (col + 1) * scale)),
                             int(std::floor(y + (row + 1) * scale)), ink);
            x += 6 * scale;
        }
    }
}
