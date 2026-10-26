#pragma once
#include "correlation.hpp"
#include <chrono>
#include <functional>
#include <string>

namespace pose::vitals {
// The caller supplies a qualified, exclusive register transport. No mmap,
// physical address guesses, DMA, SDK ownership or implicit device reset here.
class PlDotProducts final:public DotProducts {
public:
    using Read=std::function<std::uint32_t(unsigned)>;
    using Write=std::function<void(unsigned,std::uint32_t)>;
    PlDotProducts(const std::string& profile,bool deployment_qualified,Read,Write,
                  std::chrono::milliseconds timeout=std::chrono::milliseconds(250));
    std::vector<std::int64_t> calculate(const std::vector<std::int32_t>&,std::size_t) override;
    const char* name() const noexcept override { return "pl_fixed18_acf"; }
private:
    Read read_;Write write_;std::uint32_t seq_=0;bool isolated_=false;
    std::chrono::milliseconds timeout_;
};
}
