// 流媒体模块：拥有H264访问单元、有界通道和RTSP；网络对象仅由事件线程操作。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#pragma once
#include "h264_access_unit.hpp"
#include <deque>
#include <exception>
#include <mutex>

namespace pose::stream {
    // Single producer; single event-loop consumer. No live555 calls on the producer.
    // A nonblocking self-pipe wakes the event loop. Overflow fails, never drops P.
    class AccessUnitChannel {
        public:
        static constexpr size_t capacity = 8;
        AccessUnitChannel();
        ~AccessUnitChannel();
        AccessUnitChannel(const AccessUnitChannel &) = delete;
        AccessUnitChannel& operator = (const AccessUnitChannel &) = delete;
        void publish(AccessUnit);
        void close();
        void fail(std::exception_ptr);
        struct Batch {
            std::deque<AccessUnit> units;
            bool closed = false;
        };
        Batch take();
        int notificationFd() const {
            return pipe_[0];
        }

        size_t highWater() const;
        private:
        void notify();
        int pipe_[2] {
            - 1, - 1
        };
        mutable std::mutex mutex_;
        std::deque<AccessUnit> units_;
        std::exception_ptr failure_;
        bool closed_ = false;
        size_t highWater_ = 0;
    };
}
