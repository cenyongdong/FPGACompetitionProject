// 推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#include "input_read_contract.hpp"
#include <stdexcept>

namespace pose::input_read {
    void boundedRead(HostView v, size_t bytes, const std::function<void(char *, size_t) > & reader) {
        if (!v.data || !bytes || bytes > 1024 * 1024 || v.offset > v.capacity || bytes > v.capacity - v.offset || !reader) throw std::runtime_error("Input read Host destination/byte contract differs");
        reader(v.data, bytes);
        // data already points at the tensor start; no second offset.
    }

}
