// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
// Persistence owns bytes; this module has no SDK or device dependency.
#include <filesystem>
#include <string>
#include <vector>
#include <cstdint>

namespace pose::failure_evidence {
    struct Blob {
        size_t slot = 0;
        std::vector<int64_t > shape;
        std::string layout;
        size_t distributions = 0, offset = 0, chunkBytes = 0;
        std::vector<char> bytes;
    };
    void configure(const std::filesystem::path& freshDirectory);
    bool enabled();
    void save(uint64_t frame, uint64_t invocation, int64_t op, const std::string& error, const std::vector<Blob > & ownedInputs, const std::string& declarationsJson);
    void noteCaptureError(const std::string &) noexcept;
}
