#pragma once
#include "typed_scratch_pattern.hpp"
#include "typed_scratch_sdk.hpp"
#include <icraft-xrt/core/tensor.h>
namespace pose::axi_probe {
enum class Method { Copy, Read };
void transfer(const icraft::xrt::Tensor&,icraft::xrt::Tensor&,Method);
using Pair=pose::typed_scratch::Pair;
using Bytes=pose::typed_scratch::Bytes;
using Writes=pose::typed_scratch::Writes;
using pose::typed_scratch::pattern;
using pose::typed_scratch::matches;
using pose::typed_scratch::saveExpected;
class SdkScratch {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    SdkScratch(const std::filesystem::path&,const std::filesystem::path&,Method);
    ~SdkScratch();
    void readSources(Pair&);
    void writePattern(size_t,Writes&);
    void copyPair(Pair&);
};
}
