#pragma once
#include <icraft-xrt/core/backend.h>
#include <filesystem>
namespace pose::upstream_sdk {
void configure(const std::filesystem::path& fresh);
void begin(uint64_t frame,uint64_t invocation,const icraft::xrt::Device&,bool hardware);
void pre(const icraft::xir::Operation&);
void post(const icraft::xir::Operation&,const std::vector<icraft::xrt::Tensor>&);
void save();
}
