// 输入模块：固定CSI契约、完整记录重组及训练等价预处理；窗口按拥有值交接。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <array>
#include <complex>
#include <cstdint>
#include <string>

namespace pose_v1 {
    constexpr std::size_t kReceivers = 3, kAntennas = 3, kCarriers = 30, kTimes = 20;
    constexpr std::size_t kComplexCount = 3 * 3 * 30 * 20;
    constexpr std::size_t kTokenCount = 180 * 60;
    constexpr std::size_t kPayloadBytes = kComplexCount * 2 * sizeof(double);
    using RawCsi = std::array<std::complex<double>, kComplexCount>;
    using Tokens = std::array<float, kTokenCount>;
    struct Window {
        std::uint64_t frame_id = 0, source_time_ns = 0;
        RawCsi csi {};
    };
    constexpr std::size_t raw_index(std::size_t r, std::size_t a, std::size_t n, std::size_t t) {
        return(((r * kAntennas + a) * kCarriers + n) * kTimes + t);
    }

    // Exact model order: receiver, antenna, time, [30 amplitude, 30 phase].
    // 1. 按固定训练顺序生成幅度和校正相位；保留浮点运算与signed-zero行为。
    Tokens preprocess(const RawCsi& csi);
    // 2. 读取完整PIWCSI1记录，先验证头部与长度，再恢复原始复数窗口。
    Window read_window(const std::string& filename);
    // 3. 保存实际FP32输入，不执行模型推理。
    void write_tokens(const std::string& filename, const Tokens& tokens);
}
