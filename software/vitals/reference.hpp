#pragma once

#include <array>
#include <complex>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

// 独立PS参考算法，无SDK、MMIO、模型、HDMI或网络依赖。
// 输入必须是同一接收节点、同包天线对的连续记录；不做补帧或重采样。
namespace pose::vitals {
    constexpr std::size_t channels = 4;
    constexpr std::size_t max_samples = 2048;

    enum class ClockKind { UnknownArrival, VerifiedSampling, SyntheticUniform };
    struct AntennaPair {
        std::complex<double> first, second;
    };
    struct Sample {
        std::uint64_t time_ns = 0, sequence = 0;
        std::array<AntennaPair, channels> pairs {};
        bool valid = true;
    };
    struct Window {
        std::vector<Sample> samples;
        ClockKind clock = ClockKind::UnknownArrival;
    };
    struct Config {
        double sample_rate = 50.0;
        double warmup_seconds = 10.0, window_seconds = 30.0;
        double heart_low_hz = 0.8, heart_high_hz = 2.0;
        double breath_low_hz = 0.1, breath_high_hz = 0.5;
        double max_jitter_ms = 2.0, min_amplitude = 1e-12;
        double max_phase_step = 0.25, max_phase_rms = 1.0;
        double min_correlation = 0.6, min_concentration = 0.6;
        double min_heart_energy_ratio = 1e-4;
        double agreement_hz = 0.05, harmonic_guard_hz = 0.035;
        std::size_t min_agreeing_channels = 3;
    };
    struct Biquad {
        double b0, b1, b2, a1, a2;
    };
    struct Candidate {
        bool usable = false;
        double acf_hz = 0, spectral_hz = 0;
        double correlation = 0, concentration = 0, energy_ratio = 0;
        std::string reason;
    };
    struct ChannelTrace {
        std::vector<double> phase, detrended, heart, breath;
        // ACF从lag=0到指定最大lag，归一化到两段样本各自的能量。
        std::vector<double> heart_acf, breath_acf;
        Candidate heart_candidate, breath_candidate;
    };
    struct Timing {
        double quality_ms = 0, phase_ms = 0, filter_ms = 0;
        double correlation_ms = 0, spectrum_decision_ms = 0, total_ms = 0;
    };
    struct Quality {
        std::size_t samples = 0, required_samples = 0;
        std::size_t missing_sequences = 0, invalid_samples = 0;
        double jitter_p95_ms = 0, max_interval_ms = 0;
    };
    struct Estimate {
        double bpm = 0, confidence = 0;
        std::size_t agreeing_channels = 0;
    };
    struct Result {
        std::string status = "invalid";
        std::vector<std::string> reasons;
        Quality quality;
        Timing timing;
        std::optional<Estimate> heart, breath;
        std::array<ChannelTrace, channels> trace;
        std::vector<Biquad> heart_sections, breath_sections;
    };

    // 配置错误抛invalid_argument；数据不合格返回原因，不自动修补或复用旧结果。
    Result analyze(const Window& window, const Config& config = {});
    std::string clock_name(ClockKind clock);
}
