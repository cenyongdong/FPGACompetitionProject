// 推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstddef>
#include <functional>

namespace pose::input_read {
    // A pointer into an owned Host allocation. Device addresses never enter here.
    struct HostView {
        char* data;
        size_t offset, capacity;
    };
    void boundedRead(HostView destination, size_t bytes, const std::function<void(char *, size_t) > & reader);
}
