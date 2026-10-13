// 推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <icraft-xrt/core/tensor.h>

namespace pose::input_read {
    void intoHost(const icraft::xrt::Tensor& source, icraft::xrt::Tensor& destination);
}
