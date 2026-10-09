#pragma once
#include <icraft-xrt/core/tensor.h>
#include <filesystem>
#include <vector>
#include <cstdint>
namespace pose::source_diagnostic {
// Configuration performs no IO. Capture is called only after the original error
// and owned Host staging have been saved; it never advances the model.
void configure(const std::filesystem::path& freshDirectory);
void capture(uint64_t frame,uint64_t invocation,int64_t op,
             const std::vector<icraft::xrt::Tensor>& sources,
             const icraft::xrt::Device& expectedDevice,bool permitHardware,
             size_t originalStagingBytes);
}
