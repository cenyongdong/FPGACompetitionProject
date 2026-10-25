// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstdint>
#include <cstddef>
#include <chrono>
#include <filesystem>
#include <functional>
#include <string>
#include <vector>

namespace pose::stage_observation {
    uint64_t now();
    struct Completion {
        uint32_t target = 0, initial = 0, final = 0;
        size_t polls = 0;
        uint64_t begin = 0, end = 0;
    };
    Completion waitFresh(uint32_t target, uint32_t maximum, const std::function<uint32_t() > &, std::chrono::milliseconds timeout);
    struct Info {
        size_t slot = 0, bytes = 0;
        uint32_t beforeWaitCount=0, afterWaitCount=0, beforeCopyCount=0, afterCopyCount=0;
        uint64_t sourceAddress = 0, sourceOffset = 0, sourceCapacity = 0;
        uint64_t hostPointer = 0, hostChunk = 0, hostOffset = 0, hostCapacity = 0;
        uint64_t waitBegin = 0, waitEnd = 0, copyBegin = 0, copyEnd = 0;
        std::string sourceKind, sourceRegion, hostRegion;
    };
    using CopyObserver = std::function<void(uint64_t, uint64_t, int64_t, size_t, std::vector<char>)>;
    void configure(const std::filesystem::path& freshRoot, CopyObserver observer = {}, uint64_t metadata_invocation_limit = UINT64_MAX);
    std::filesystem::path failureRoot();
    void saveMetadata();
    void recordCompletion(uint64_t frame, uint64_t invocation, int64_t op, const Completion &);
    void recordSyncFailure(uint64_t frame, uint64_t invocation, int64_t op, const char *);
    class Call {
        struct Entry {
            Info info;
            uint64_t begin, end;
            std::vector<char> bytes;
        };
        uint64_t frame_, invocation_;
        int64_t op_;
        size_t total_ = 0;
        std::vector<Entry > entries_;
        public:
        Call(uint64_t frame, uint64_t invocation, int64_t op) : frame_(frame), invocation_(invocation), op_(op) {} void afterCopy(Info, const char* ownedHostPointer);
        void validate() const;
        void saveFailure(const std::filesystem::path& savedHostFailureRoot, uint64_t errorTime) const;
    };
}
