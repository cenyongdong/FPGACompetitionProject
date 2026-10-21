#include "reference.hpp"
#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>

namespace {
    using namespace pose::vitals;
    constexpr double pi = 3.14159265358979323846;
    void need(bool ok, const char* why) { if (!ok) throw std::runtime_error(why); }
    Window signal(double heart = 1.2, double breath = 0.25, double rate = 50) {
        Window w;
        w.clock = ClockKind::SyntheticUniform;
        for (std::size_t n = 0; n < static_cast<std::size_t>(40 * rate); ++n) {
            Sample s;
            s.time_ns = static_cast<std::uint64_t>(std::llround(n * 1e9 / rate));
            s.sequence = n + 1;
            const double t = n / rate;
            for (std::size_t ch = 0; ch < channels; ++ch) {
                const auto p = 0.3 * std::sin(2 * pi * breath * t + ch * 0.1) +
                    0.03 * std::sin(2 * pi * heart * t + ch * 0.2);
                // 两天线共同相位随时间改变，差分应消去该项。
                const auto common = 3.0 * std::sin(2 * pi * 0.7 * t);
                s.pairs[ch] = {std::polar(1.0, common + p), std::polar(0.8, common)};
            }
            w.samples.push_back(s);
        }
        return w;
    }
    bool has(const Result& r, const char* reason) {
        for (const auto& x : r.reasons) if (x == reason) return true;
        return false;
    }
}

int main() {
    std::size_t passed = 0;
    auto run = [&](const char* name, const std::function<void()>& test) {
        try { test(); ++passed; std::cout << "PASS " << name << '\n'; }
        catch (const std::exception& e) { throw std::runtime_error(std::string(name) + ": " + e.what()); }
    };
    try {
        run("known_rates_and_common_phase", [] {
            const auto r = analyze(signal());
            need(r.heart && std::abs(r.heart->bpm - 72) < 1.0, "72bpm not recovered");
            need(r.breath && std::abs(r.breath->bpm - 15) < 0.5, "15/min not recovered");
        });
        run("unknown_clock", [] {
            auto w = signal(); w.clock = ClockKind::UnknownArrival;
            const auto r = analyze(w);
            need(!r.heart && has(r, "unverified_sample_clock"), "arrival time treated as source clock");
        });
        run("short_history", [] {
            auto w = signal(); w.samples.resize(100);
            need(has(analyze(w), "incomplete_window"), "short history accepted");
        });
        run("missing_sequence", [] {
            auto w = signal();
            for (std::size_t i = 1000; i < w.samples.size(); ++i) ++w.samples[i].sequence;
            need(has(analyze(w), "missing_sequence"), "lost sample accepted");
        });
        run("duplicate_time", [] {
            auto w = signal(); w.samples[100].time_ns = w.samples[99].time_ns;
            need(has(analyze(w), "non_monotonic_time"), "duplicate timestamp accepted");
        });
        run("jitter", [] {
            auto w = signal(); w.samples[100].time_ns += 5000000;
            need(has(analyze(w), "non_uniform_sampling"), "uneven clock accepted");
        });
        run("nonfinite", [] {
            auto w = signal(); w.samples[5].pairs[0].first.real(std::numeric_limits<double>::quiet_NaN());
            need(has(analyze(w), "non_finite_input"), "NaN accepted");
        });
        run("zero_amplitude", [] {
            auto w = signal(); w.samples[5].pairs[0].first = 0;
            need(has(analyze(w), "insufficient_amplitude"), "zero phase source accepted");
        });
        run("motion", [] {
            auto w = signal();
            for (std::size_t i = 1000; i < w.samples.size(); ++i)
                for (auto& p : w.samples[i].pairs) p.first *= std::polar(1.0, 1.0);
            need(has(analyze(w), "motion_or_phase_jump"), "motion step accepted");
        });
        run("unsupported_config", [] {
            Config c; c.sample_rate = 1;
            bool rejected = false;
            try { analyze(signal(), c); } catch (const std::invalid_argument&) { rejected = true; }
            need(rejected, "invalid rate accepted");
        });
        run("large_finite_input", [] {
            auto w = signal();
            for (auto& s : w.samples) for (auto& p : s.pairs) { p.first *= 1e200; p.second *= 1e200; }
            const auto r = analyze(w);
            need(r.heart && std::abs(r.heart->bpm - 72) < 1, "finite scaling overflow");
        });
        run("sample_budget", [] {
            auto w = signal();
            while (w.samples.size() <= max_samples) w.samples.push_back(w.samples.back());
            need(has(analyze(w), "sample_budget_exceeded"), "oversize window accepted");
        });
        run("unknown_enum_clock", [] {
            auto w = signal(); w.clock = static_cast<ClockKind>(99);
            need(has(analyze(w), "unverified_sample_clock"), "unknown clock accepted");
        });
        run("cardiac_fundamental_below_double_period_peak", [] {
            for (const auto spec : {std::array<double, 2>{10, 110.0 / 60}, {25, 2.0}}) {
                Config c; c.sample_rate = spec[0];
                const auto r = analyze(signal(spec[1], 0.27, spec[0]), c);
                need(r.heart && std::abs(r.heart->bpm - spec[1] * 60) < 1,
                     "supported fundamental lost to double-period peak");
                for (const auto& trace : r.trace) {
                    const auto& h = trace.heart_candidate;
                    need(h.usable && h.correlation >= c.min_correlation &&
                         std::abs(h.acf_hz - h.spectral_hz) <= c.agreement_hz,
                         "fundamental accepted without original quality evidence");
                }
            }
        });
        run("breath_fundamental_enables_harmonic_guard", [] {
            for (const double rate : {10., 20., 25., 50.}) {
                Config c; c.sample_rate = rate;
                const auto r = analyze(signal(2.0, 0.25, rate), c);
                need(r.breath && std::abs(r.breath->bpm - 15) < 0.1,
                     "supported breath fundamental not recovered");
                need(!r.heart, "breathing harmonic published as cardiac evidence");
            }
        });
        std::cout << "PASSED " << passed << '\n';
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
