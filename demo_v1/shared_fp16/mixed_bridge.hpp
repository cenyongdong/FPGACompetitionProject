// 推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include "host_cpu_adapter.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <cstdint>
#include <iosfwd>

namespace pose_v1::mixed_candidate {
    void configure(std::ostream* log, bool hardware, icraft::xrt::Device device = {});
    void set_frame(uint64_t frame, uint64_t invocation = 0);
    void tensor_info(std::ostream &, const icraft::xrt::Tensor &);
    void register_ops(const icraft::xir::Network &, icraft::xrt::HostBackend);
    std::vector<icraft::xrt::Tensor> forward(const icraft::xir::Operation &, const std::vector<icraft::xrt::Tensor> &, const std::vector<icraft::xrt::Tensor> &);
}

int mixed_host_check(int argc, char * * argv);
