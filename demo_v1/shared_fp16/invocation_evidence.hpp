// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include <cstdint>
#include <exception>
#include <filesystem>
#include <functional>
#include <map>
#include <string>
#include <thread>
#include <vector>
// SDK-free, single-owner evidence. No device pointer, synchronization or math.
namespace pose::invocation_evidence {
    class Frame {
        const std::thread::id owner_ = std::this_thread::get_id();
        void checkOwner() const;
        struct Item {
            int64_t op;
            size_t slot;
            std::vector<char> bytes;
        };
        uint64_t frame_ = 0, invocation_ = 0;
        bool active_ = false;
        size_t total_ = 0;
        std::map<std::pair<int64_t, size_t>, Item > items_;
        public:
        void begin(uint64_t frame, uint64_t invocation);
        void record(int64_t op, size_t slot, std::vector<char> ownedBytes);
        void save(const std::filesystem::path& freshDirectory) const;
        size_t bytes() const {
            return total_;
        }

        size_t inputs() const {
            return items_.size();
        }

    };
    struct Task {
        std::string name;
        std::function<void() > persist;
    };
    // Execute every bounded task even if one rethrows an output gate. Retain the
    // original computation exception; persistence errors never silently replace it.
    void flush(const std::vector<Task > &, std::exception_ptr& original, const std::filesystem::path& freshLedger);
}
