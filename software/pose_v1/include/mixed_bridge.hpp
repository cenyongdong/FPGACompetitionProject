#pragma once
#include "host_cpu_adapter.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <cstdint>
#include <iosfwd>

namespace pose_v1::mixed_candidate {
void configure(std::ostream* log, bool hardware, icraft::xrt::Device device = {});
void set_frame(uint64_t frame, uint64_t invocation = 0);
void tensor_info(std::ostream&, const icraft::xrt::Tensor&);
void register_ops(const icraft::xir::Network&, icraft::xrt::HostBackend);
std::vector<icraft::xrt::Tensor> forward(const icraft::xir::Operation&,
    const std::vector<icraft::xrt::Tensor>&, const std::vector<icraft::xrt::Tensor>&);
}

int mixed_host_check(int argc, char** argv);
