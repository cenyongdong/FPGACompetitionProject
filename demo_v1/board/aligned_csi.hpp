#pragma once
#include "preprocess.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace demo_v1 {
    constexpr size_t csi_record_bytes = 86432;
    inline uint64_t u64(const unsigned char* p) {
        uint64_t n = 0;
        for (unsigned i = 0; i < 8; ++i) n |= uint64_t(p[i]) << (8 * i);
        return n;
    }
    inline uint32_t u32(const unsigned char* p) {
        uint32_t n = 0;
        for (unsigned i = 0; i < 4; ++i) n |= uint32_t(p[i]) << (8 * i);
        return n;
    }
    inline void put64(unsigned char* p, uint64_t n) {
        for (unsigned i = 0; i < 8; ++i) p[i] = static_cast<unsigned char>(n >> (8 * i));
    }
    inline void put32(unsigned char* p, uint32_t n) {
        for (unsigned i = 0; i < 4; ++i) p[i] = static_cast<unsigned char>(n >> (8 * i));
    }
    // 外部R/A/T/N布局；仅交换时间和子载波轴，复数精度及原预处理保持。
    inline pose_v1::Window decode_aligned(const std::vector<unsigned char>& bytes) {
        if (bytes.size() != csi_record_bytes || std::memcmp(bytes.data(), "PIWCSI2\0", 8)
            || u32(bytes.data() + 8) != 2 || u32(bytes.data() + 12) != 86400)
            throw std::runtime_error("Invalid aligned CSI v2 record");
        pose_v1::Window window;
        window.frame_id = u64(bytes.data() + 16);
        window.source_time_ns = u64(bytes.data() + 24);
        for (size_t r = 0; r < 3; ++r) for (size_t a = 0; a < 3; ++a)
            for (size_t t = 0; t < 20; ++t) for (size_t n = 0; n < 30; ++n) {
                const auto offset = 32 + (((r * 3 + a) * 20 + t) * 30 + n) * 16;
                double re, im;
                std::memcpy(&re, bytes.data() + offset, 8);
                std::memcpy(&im, bytes.data() + offset + 8, 8);
                if (!std::isfinite(re) || !std::isfinite(im)) throw std::runtime_error("Non-finite CSI");
                window.csi[pose_v1::raw_index(r, a, n, t)] = {re, im};
            }
        return window;
    }
}
