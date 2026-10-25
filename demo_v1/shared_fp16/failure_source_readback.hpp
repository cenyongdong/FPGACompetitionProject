// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <icraft-xrt/core/tensor.h>
#include <filesystem>
#include <vector>
#include <cstdint>

namespace pose::source_diagnostic {
    // Configuration performs no IO. Capture is called only after the original error
    // and owned Host staging have been saved; it never advances the model.
    void configure(const std::filesystem::path& freshDirectory);
    // 失败后只读取证：先校验存储身份并拥有全部目标缓冲，再连续执行两轮SDK read。
    void capture(uint64_t frame, uint64_t invocation, int64_t op, const std::vector<icraft::xrt::Tensor> & sources, const icraft::xrt::Device& expectedDevice, bool permitHardware, size_t originalStagingBytes);
}
