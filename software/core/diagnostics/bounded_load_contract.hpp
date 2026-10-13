// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstddef>
#include <cstdint>
#include <stdexcept>

namespace pose::bounded_load {
    constexpr size_t sentLimit = 103, warmups = 3, fixtureCount = 27;
    constexpr uint64_t transportBase = 100000, readyDurationNs = 30000000000ULL;
    constexpr unsigned networkSeconds = 100, clientSeconds = 105;
    inline size_t fixtureIndex(uint64_t id) {
        if (id < transportBase || id - transportBase >= sentLimit) throw std::runtime_error("Bounded103 transport outside range");
        return size_t(id - transportBase) % fixtureCount;
    }

    inline bool keepReference(size_t invocation, size_t total, bool firstSource) {
        if (total > sentLimit || invocation >= total) throw std::runtime_error("Bounded reference index outside range");
        return firstSource || invocation == 0 || invocation == fixtureCount || invocation + 1 == total;
    }

}
