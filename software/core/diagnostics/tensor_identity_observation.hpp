// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <thread>
#include <vector>

namespace pose::tensor_identity {
    struct Storage {
        uint64_t tensor = 0, region = 0, chunk = 0, device = 0, address = 0, offset = 0, capacity = 0, bytes = 0;
        bool ownerMatches = false, declaredMatches = false;
        std::string kind, regionKey, type, declaredType;
    };
    struct Pair {
        Storage source, destination;
        bool sameRegion = false, sameDevice = false;
    };
    class Recorder {
        struct Row {
            uint64_t frame, invocation, time;
            int64_t op;
            size_t slot;
            bool after;
            Pair pair;
            std::string error;
        };
        std::thread::id owner_ = std::this_thread::get_id();
        std::vector<Row > rows_;
        bool pending_ = false;
        size_t total_ = 0;
        public:
        void sample(uint64_t frame, uint64_t invocation, int64_t op, size_t slot, bool after, Pair);
        void save(const std::filesystem::path &) const;
    };
    void configure(const std::filesystem::path &);
    bool enabled();
    void sample(uint64_t, uint64_t, int64_t, size_t, bool, Pair);
    void save();
}
