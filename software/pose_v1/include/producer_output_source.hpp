#pragma once
#include "producer_output_lease.hpp"
#include <icraft-xrt/core/tensor.h>
#include <array>
#include <vector>
namespace pose::producer_read {
std::shared_ptr<ReadScope> createScope();
void checkIdle(const std::shared_ptr<ReadScope>&);
std::unique_ptr<OutputLease> makeLease(const std::shared_ptr<ReadScope>&,
    std::vector<icraft::xrt::Tensor>,const std::array<icraft::xir::TensorType,2>&,
    const icraft::xrt::Device&,size_t invocation);
void expireScope(const std::shared_ptr<ReadScope>&,const std::filesystem::path&);
}
