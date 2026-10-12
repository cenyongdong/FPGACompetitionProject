#pragma once
#include <icraft-xrt/core/tensor.h>
#include <filesystem>
#include <vector>
namespace pose::final_source_sdk {
void configure(const std::filesystem::path& fresh);
void begin(uint64_t frame,uint64_t invocation);
void source(int64_t op,size_t slot,const icraft::xrt::Tensor&,const icraft::xrt::Tensor& host,const icraft::xir::TensorType& declared,const icraft::xrt::Device&,bool permit);
void outputs(int64_t op,const std::vector<icraft::xrt::Tensor>&);
void capture(const std::string& originalError);
}
