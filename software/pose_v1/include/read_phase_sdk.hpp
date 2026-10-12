#pragma once
#include <icraft-xrt/core/tensor.h>
#include <filesystem>
namespace pose::read_phase_sdk {
void configure(const std::filesystem::path& fresh);
void copy(uint64_t frame,uint64_t invocation,const icraft::xrt::Tensor& source,icraft::xrt::Tensor& destination,bool sourceHost);
void beforeCPU(const icraft::xrt::Tensor& staged);
void error(const std::string& original);
void save();
}
