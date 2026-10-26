#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>
#include <string>

namespace pose::vitals {
// PS owns scaling, normalization and physiological decisions. A PL implementation
// receives only bounded signed integers and returns exact dot products.
class CorrelationBackend {
public:
    virtual ~CorrelationBackend() = default;
    virtual std::vector<double> correlate(const std::vector<double>&, std::size_t last) = 0;
    virtual const char* name() const noexcept = 0;
};
std::vector<double> floating_correlation(const std::vector<double>&, std::size_t last);
class DotProducts {
public:
    virtual ~DotProducts() = default;
    virtual std::vector<std::int64_t> calculate(const std::vector<std::int32_t>&, std::size_t last) = 0;
    virtual const char* name() const noexcept = 0;
};
class ScalarDots final : public DotProducts {
public:
    std::vector<std::int64_t> calculate(const std::vector<std::int32_t>&, std::size_t) override;
    const char* name() const noexcept override { return "fixed18_cpu_reference"; }
};
class FixedCorrelation final : public CorrelationBackend {
    DotProducts& dots_;
public:
    explicit FixedCorrelation(DotProducts& dots): dots_(dots) {}
    std::vector<double> correlate(const std::vector<double>&, std::size_t) override;
    const char* name() const noexcept override { return dots_.name(); }
};
// Non-owning: a failed PL transport remains owned by its deployment controller.
// CPU fallback never retries, resets, unmaps or releases an in-flight device.
class FallbackCorrelation final : public CorrelationBackend {
    CorrelationBackend& primary_;
    bool isolated_=false;
    std::string fault_;
public:
    explicit FallbackCorrelation(CorrelationBackend& primary):primary_(primary){}
    std::vector<double> correlate(const std::vector<double>&,std::size_t) override;
    const char* name() const noexcept override { return isolated_?"float64_cpu_after_backend_fault":primary_.name(); }
    const std::string& fault() const noexcept { return fault_; }
};
constexpr std::size_t acf_max_samples=2048, acf_max_lag=511;
constexpr std::int32_t acf_peak=65535;
void validate_dot_input(const std::vector<std::int32_t>&, std::size_t);
}
