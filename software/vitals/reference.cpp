#include "reference.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>
#include <stdexcept>

namespace pose::vitals {
    namespace {
        constexpr double pi = 3.141592653589793238462643383279502884;
        using Clock = std::chrono::steady_clock;
        double elapsed(Clock::time_point begin) {
            return std::chrono::duration<double, std::milli>(Clock::now() - begin).count();
        }
        double median(std::vector<double> values) {
            std::sort(values.begin(), values.end());
            const auto n = values.size();
            return n % 2 ? values[n / 2] : (values[n / 2 - 1] + values[n / 2]) * 0.5;
        }
        void reason(Result& result, const std::string& value) {
            if (std::find(result.reasons.begin(), result.reasons.end(), value) == result.reasons.end())
                result.reasons.push_back(value);
        }
        std::size_t count(double seconds, double rate) {
            const auto value = seconds * rate;
            if (!std::isfinite(value) || value < 1 || value > max_samples ||
                std::abs(value - std::round(value)) > 1e-8)
                throw std::invalid_argument("Duration times rate must be an integer in 1..2048");
            return static_cast<std::size_t>(std::llround(value));
        }
        bool finite(double x) { return std::isfinite(x); }
        void validate(const Config& c) {
            const double values[] = {c.sample_rate, c.warmup_seconds, c.window_seconds,
                c.heart_low_hz, c.heart_high_hz, c.breath_low_hz, c.breath_high_hz,
                c.max_jitter_ms, c.min_amplitude, c.max_phase_step, c.max_phase_rms,
                c.min_correlation, c.min_concentration, c.min_heart_energy_ratio,
                c.agreement_hz, c.harmonic_guard_hz};
            for (const auto x : values) if (!finite(x) || x <= 0)
                throw std::invalid_argument("Configuration fields must be finite and positive");
            if (c.breath_low_hz >= c.breath_high_hz || c.heart_low_hz >= c.heart_high_hz ||
                c.breath_high_hz >= c.heart_low_hz || c.heart_high_hz >= c.sample_rate * 0.5 ||
                c.window_seconds * c.breath_low_hz < 3.0 - 1e-9 ||
                c.min_agreeing_channels < 2 || c.min_agreeing_channels > channels ||
                c.min_correlation > 1 || c.min_concentration > 1 || c.min_heart_energy_ratio > 1 ||
                c.max_jitter_ms >= 500.0 / c.sample_rate)
                throw std::invalid_argument("Unsupported bands, window, quality or consensus configuration");
            if (count(c.warmup_seconds, c.sample_rate) + count(c.window_seconds, c.sample_rate) > max_samples)
                throw std::invalid_argument("Warmup plus estimation window exceeds 2048 samples");
        }

        // Butterworth极点对的双线性变换，a0归一化。
        // 高通与低通分别设计，不声称等于同阶Butterworth带通设计。
        Biquad section(double hz, double rate, bool highpass, double q = 1 / std::sqrt(2.0)) {
            const auto w = 2 * pi * hz / rate;
            const auto cosine = std::cos(w), alpha = std::sin(w) / (2 * q);
            const auto a0 = 1 + alpha;
            const auto b0 = (highpass ? 1 + cosine : 1 - cosine) * 0.5 / a0;
            return {b0, (highpass ? -2 : 2) * b0, b0,
                -2 * cosine / a0, (1 - alpha) / a0};
        }
        std::vector<double> filter(std::vector<double> values, const std::vector<Biquad>& sections) {
            for (const auto& c : sections) {
                double z1 = 0, z2 = 0;
                for (auto& x : values) {
                    const double y = c.b0 * x + z1;
                    z1 = c.b1 * x - c.a1 * y + z2;
                    z2 = c.b2 * x - c.a2 * y;
                    if (!finite(y) || !finite(z1) || !finite(z2))
                        throw std::runtime_error("Non-finite filter state; stop this analysis");
                    x = y;
                }
            }
            return values;
        }
        std::vector<double> detrend(const std::vector<double>& x) {
            const double center = (x.size() - 1) * 0.5;
            const double mean = std::accumulate(x.begin(), x.end(), 0.0) / x.size();
            double xy = 0, xx = 0;
            for (std::size_t i = 0; i < x.size(); ++i) {
                const auto t = static_cast<double>(i) - center;
                xy += t * (x[i] - mean);
                xx += t * t;
            }
            const double slope = xy / xx;
            std::vector<double> output(x.size());
            for (std::size_t i = 0; i < x.size(); ++i)
                output[i] = x[i] - mean - slope * (static_cast<double>(i) - center);
            return output;
        }
        std::vector<double> acf(const std::vector<double>& x, std::size_t last) {
            std::vector<double> output(last + 1);
            for (std::size_t k = 0; k <= last; ++k) {
                double product = 0, first = 0, second = 0;
                for (std::size_t i = k; i < x.size(); ++i) {
                    product += x[i] * x[i - k];
                    first += x[i] * x[i];
                    second += x[i - k] * x[i - k];
                }
                const auto norm = std::sqrt(first) * std::sqrt(second);
                output[k] = norm > 1e-24 ? product / norm : 0;
            }
            return output;
        }

        // 用未带通的去趋势原信号验证周期证据，防止带通滤波将噪声变成“心搏”。
        struct Spectrum { std::vector<double> power; double step; };
        Spectrum spectrum(const std::vector<double>& x, double rate) {
            std::size_t n = 1;
            while (n < x.size() * 4) n <<= 1;
            std::vector<std::complex<double>> data(n);
            for (std::size_t i = 0; i < x.size(); ++i)
                data[i] = x[i] * (0.5 - 0.5 * std::cos(2 * pi * i / (x.size() - 1)));
            for (std::size_t i = 1, j = 0; i < n; ++i) {
                std::size_t bit = n >> 1;
                for (; j & bit; bit >>= 1) j ^= bit;
                j ^= bit;
                if (i < j) std::swap(data[i], data[j]);
            }
            for (std::size_t len = 2; len <= n; len <<= 1) {
                const auto root = std::polar(1.0, -2 * pi / len);
                for (std::size_t base = 0; base < n; base += len) {
                    std::complex<double> w = 1;
                    for (std::size_t j = 0; j < len / 2; ++j) {
                        const auto even = data[base + j], odd = data[base + j + len / 2] * w;
                        data[base + j] = even + odd;
                        data[base + j + len / 2] = even - odd;
                        w *= root;
                    }
                }
            }
            Spectrum out{{}, rate / n};
            out.power.reserve(n / 2 + 1);
            for (std::size_t i = 0; i <= n / 2; ++i) out.power.push_back(std::norm(data[i]));
            return out;
        }
        double band_energy(const Spectrum& s, double low, double high) {
            double sum = 0;
            for (std::size_t i = 1; i < s.power.size(); ++i)
                if (i * s.step >= low && i * s.step <= high) sum += s.power[i];
            return sum;
        }
        double interpolate(double left, double middle, double right) {
            const auto denominator = left - 2 * middle + right;
            if (denominator >= -1e-15) return 0;
            return std::clamp(0.5 * (left - right) / denominator, -0.5, 0.5);
        }
        Candidate detect(const std::vector<double>& filtered,
                         const std::vector<double>& correlations, const Spectrum& s,
                         double low, double high, const Config& c, bool cardiac) {
            Candidate out;
            auto reject = [&](const char* why) { out.reason = why; return out; };
            double energy = 0;
            for (const auto x : filtered) energy += x * x;
            if (energy / filtered.size() < 1e-14) return reject("no_band_energy");
            const auto first = static_cast<std::size_t>(std::floor(c.sample_rate / high));
            const auto last = static_cast<std::size_t>(std::ceil(c.sample_rate / low));
            const auto local_peak = [&](std::size_t k) {
                return correlations[k] > correlations[k - 1] && correlations[k] >= correlations[k + 1];
            };
            std::size_t best = 0;
            // 两端也有邻点，避免单调ACF在搜索边界被误当作峰。
            for (std::size_t k = std::max<std::size_t>(1, first); k <= last; ++k)
                if (local_peak(k) && (!best || correlations[k] > correlations[best])) best = k;
            if (!best) return reject("no_local_acf_peak");
            out.correlation = correlations[best];
            if (out.correlation < c.min_correlation) return reject("weak_acf");
            const auto delta = interpolate(correlations[best - 1], correlations[best], correlations[best + 1]);
            out.acf_hz = c.sample_rate / (best + delta);
            std::size_t bin = 0;
            const double tolerance = s.step * 0.5;
            for (std::size_t i = 1; i + 1 < s.power.size(); ++i)
                if (i * s.step >= low - s.step && i * s.step <= high + s.step &&
                    s.power[i] > s.power[i - 1] && s.power[i] >= s.power[i + 1] &&
                    (!bin || s.power[i] > s.power[bin])) bin = i;
            if (!bin) return reject("no_raw_spectral_peak");
            const auto logpower = [&](std::size_t i) { return std::log(std::max(s.power[i], 1e-300)); };
            out.spectral_hz = (bin + interpolate(logpower(bin - 1), logpower(bin), logpower(bin + 1))) * s.step;
            {
                // 离散lag可使两倍周期峰略高于基频峰。只在真实局部ACF峰中
                // 选择同时满足原相关、频带和原谱一致性门的候选，不倍乘频率。
                // 呼吸支路同样处理，以免呼吸漏检绕过后续心率谐波拒绝。
                // 没有支持时保留原最高峰诊断，并由下面的原质量门拒绝。
                std::size_t supported = 0;
                for (std::size_t k = std::max<std::size_t>(1, first); k <= last; ++k) {
                    if (!local_peak(k) || correlations[k] < c.min_correlation) continue;
                    const auto shift = interpolate(correlations[k - 1], correlations[k], correlations[k + 1]);
                    const auto hz = c.sample_rate / (k + shift);
                    if (hz < low - tolerance || hz > high + tolerance ||
                        std::abs(hz - out.spectral_hz) > c.agreement_hz) continue;
                    if (!supported || correlations[k] > correlations[supported]) supported = k;
                }
                if (supported) {
                    const auto shift = interpolate(correlations[supported - 1], correlations[supported], correlations[supported + 1]);
                    out.acf_hz = c.sample_rate / (supported + shift);
                    out.correlation = correlations[supported];
                }
            }
            if (out.spectral_hz < low - tolerance || out.spectral_hz > high + tolerance ||
                out.acf_hz < low - tolerance || out.acf_hz > high + tolerance)
                return reject("outside_supported_band");
            if (std::abs(out.acf_hz - out.spectral_hz) > c.agreement_hz)
                return reject("acf_spectrum_disagree");
            const auto total = band_energy(s, low, high);
            const auto peak = band_energy(s, std::max(low, out.spectral_hz - 2 / c.window_seconds),
                                           std::min(high, out.spectral_hz + 2 / c.window_seconds));
            out.concentration = total > 0 ? peak / total : 0;
            if (out.concentration < c.min_concentration) return reject("diffuse_raw_spectrum");
            const auto broad = band_energy(s, 0.05, std::min(5.0, c.sample_rate * 0.5));
            out.energy_ratio = broad > 0 ? total / broad : 0;
            if (cardiac && out.energy_ratio < c.min_heart_energy_ratio)
                return reject("no_raw_cardiac_evidence");
            out.usable = true;
            out.reason = "candidate";
            return out;
        }
        std::optional<Estimate> consensus(const std::array<ChannelTrace, channels>& trace,
                                          bool heart, const Config& c) {
            std::vector<Candidate> best;
            for (const auto& anchor : trace) {
                const auto& a = heart ? anchor.heart_candidate : anchor.breath_candidate;
                if (!a.usable) continue;
                std::vector<Candidate> group;
                for (const auto& channel : trace) {
                    const auto& b = heart ? channel.heart_candidate : channel.breath_candidate;
                    if (b.usable && std::abs(a.spectral_hz - b.spectral_hz) <= c.agreement_hz)
                        group.push_back(b);
                }
                if (group.size() > best.size()) best = group;
            }
            if (best.size() < c.min_agreeing_channels) return std::nullopt;
            std::vector<double> rates, confidence;
            for (const auto& candidate : best) {
                // ACF证明周期存在；未带通谱峰提供频率，避免残留呼吸使ACF峰偏移。
                rates.push_back(candidate.spectral_hz * 60);
                confidence.push_back(candidate.correlation * std::sqrt(candidate.concentration));
            }
            return Estimate{median(rates), std::clamp(median(confidence) * best.size() / channels, 0.0, 1.0), best.size()};
        }
    }

    std::string clock_name(ClockKind clock) {
        switch (clock) {
            case ClockKind::VerifiedSampling: return "verified_sampling";
            case ClockKind::SyntheticUniform: return "synthetic_uniform";
            default: return "unknown_arrival";
        }
    }

    Result analyze(const Window& window, const Config& c) {
        validate(c);
        const auto begin = Clock::now();
        Result result;
        const auto warmup = count(c.warmup_seconds, c.sample_rate);
        const auto length = count(c.window_seconds, c.sample_rate);
        const auto required = warmup + length;
        auto& q = result.quality;
        q.samples = window.samples.size();
        q.required_samples = required;
        if (window.clock != ClockKind::VerifiedSampling && window.clock != ClockKind::SyntheticUniform)
            reason(result, "unverified_sample_clock");
        if (q.samples != required) reason(result, "incomplete_window");
        if (q.samples > max_samples) reason(result, "sample_budget_exceeded");
        std::vector<double> jitter;
        for (std::size_t i = 0; i < window.samples.size() && i < max_samples; ++i) {
            const auto& sample = window.samples[i];
            if (!sample.valid) ++q.invalid_samples;
            if (i) {
                const auto& before = window.samples[i - 1];
                if (sample.time_ns <= before.time_ns) reason(result, "non_monotonic_time");
                else {
                    const auto interval = (sample.time_ns - before.time_ns) / 1e6;
                    q.max_interval_ms = std::max(q.max_interval_ms, interval);
                    jitter.push_back(std::abs(interval - 1000.0 / c.sample_rate));
                }
                if (sample.sequence <= before.sequence) reason(result, "non_monotonic_sequence");
                else if (sample.sequence - before.sequence != 1) {
                    q.missing_sequences += static_cast<std::size_t>(sample.sequence - before.sequence - 1);
                    reason(result, "missing_sequence");
                }
            }
            for (const auto& pair : sample.pairs) {
                for (const auto z : {pair.first, pair.second}) {
                    if (!finite(z.real()) || !finite(z.imag())) reason(result, "non_finite_input");
                    else if (std::max(std::abs(z.real()), std::abs(z.imag())) < c.min_amplitude)
                        reason(result, "insufficient_amplitude");
                }
            }
        }
        if (q.invalid_samples) reason(result, "invalid_samples");
        if (!jitter.empty()) {
            std::sort(jitter.begin(), jitter.end());
            q.jitter_p95_ms = jitter[static_cast<std::size_t>(std::ceil(jitter.size() * 0.95)) - 1];
            if (jitter.back() > c.max_jitter_ms) reason(result, "non_uniform_sampling");
        }
        result.timing.quality_ms = elapsed(begin);
        if (!result.reasons.empty()) {
            result.timing.total_ms = elapsed(begin);
            return result;
        }
        // 四阶高通的两个Butterworth极点对，抑制强呼吸泄漏后再二阶低通。
        // 原二阶高通在已保存的正样例中使ACF偏向呼吸谐波，不能靠降低质量门放行。
        result.heart_sections = {
            section(c.heart_low_hz, c.sample_rate, true, 1 / (2 * std::cos(pi / 8))),
            section(c.heart_low_hz, c.sample_rate, true, 1 / (2 * std::cos(3 * pi / 8))),
            section(c.heart_high_hz, c.sample_rate, false)};
        result.breath_sections = {section(c.breath_low_hz, c.sample_rate, true), section(c.breath_high_hz, c.sample_rate, false)};
        auto stage = Clock::now();
        for (std::size_t ch = 0; ch < channels; ++ch) {
            auto& trace = result.trace[ch];
            trace.phase.reserve(required);
            double previous = 0, accumulated = 0;
            for (std::size_t i = 0; i < required; ++i) {
                const auto& pair = window.samples[i].pairs[ch];
                // 正的实数缩放不改变相位，防止大有限I/Q相乘溢出。
                const auto a = pair.first / std::max(std::abs(pair.first.real()), std::abs(pair.first.imag()));
                const auto b = pair.second / std::max(std::abs(pair.second.real()), std::abs(pair.second.imag()));
                const auto phase = std::arg(a * std::conj(b));
                if (!i) accumulated = phase;
                else {
                    double delta = std::remainder(phase - previous, 2 * pi);
                    if (delta == -pi && phase - previous > 0) delta = pi;
                    if (std::abs(delta) > c.max_phase_step) reason(result, "motion_or_phase_jump");
                    accumulated += delta;
                }
                trace.phase.push_back(accumulated);
                previous = phase;
            }
            trace.detrended = detrend(trace.phase);
            double sum = 0;
            for (const auto x : trace.detrended) sum += x * x;
            if (std::sqrt(sum / required) > c.max_phase_rms) reason(result, "excessive_phase_variation");
        }
        result.timing.phase_ms = elapsed(stage);
        if (!result.reasons.empty()) {
            result.timing.total_ms = elapsed(begin);
            return result;
        }
        stage = Clock::now();
        for (auto& trace : result.trace) {
            const auto heart = filter(trace.detrended, result.heart_sections);
            const auto breath = filter(trace.detrended, result.breath_sections);
            trace.heart.assign(heart.begin() + warmup, heart.end());
            trace.breath.assign(breath.begin() + warmup, breath.end());
        }
        result.timing.filter_ms = elapsed(stage);
        stage = Clock::now();
        for (auto& trace : result.trace) {
            trace.heart_acf = acf(trace.heart, static_cast<std::size_t>(std::ceil(c.sample_rate / c.heart_low_hz)) + 1);
            trace.breath_acf = acf(trace.breath, static_cast<std::size_t>(std::ceil(c.sample_rate / c.breath_low_hz)) + 1);
        }
        result.timing.correlation_ms = elapsed(stage);
        stage = Clock::now();
        for (auto& trace : result.trace) {
            std::vector<double> raw(trace.detrended.begin() + warmup, trace.detrended.end());
            const auto s = spectrum(raw, c.sample_rate);
            trace.breath_candidate = detect(trace.breath, trace.breath_acf, s, c.breath_low_hz, c.breath_high_hz, c, false);
            trace.heart_candidate = detect(trace.heart, trace.heart_acf, s, c.heart_low_hz, c.heart_high_hz, c, true);
        }
        result.breath = consensus(result.trace, false, c);
        if (result.breath) {
            const auto breath_hz = result.breath->bpm / 60;
            for (auto& trace : result.trace) {
                auto& heart = trace.heart_candidate;
                if (!heart.usable) continue;
                const auto harmonic = static_cast<int>(std::lround(heart.spectral_hz / breath_hz));
                if (harmonic >= 2 && harmonic <= 20 &&
                    std::abs(heart.spectral_hz - harmonic * breath_hz) <= c.harmonic_guard_hz) {
                    heart.usable = false;
                    heart.reason = "ambiguous_breathing_harmonic";
                }
            }
        }
        result.heart = consensus(result.trace, true, c);
        if (!result.heart) reason(result, "no_supported_heart_consensus");
        if (!result.breath) reason(result, "no_supported_breath_consensus");
        result.status = result.heart ? "valid" : "no_heart_estimate";
        result.timing.spectrum_decision_ms = elapsed(stage);
        result.timing.total_ms = elapsed(begin);
        return result;
    }
}
