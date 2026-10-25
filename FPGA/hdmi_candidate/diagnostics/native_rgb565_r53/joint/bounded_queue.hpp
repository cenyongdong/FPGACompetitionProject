#pragma once
#include <algorithm>
#include <condition_variable>
#include <chrono>
#include <deque>
#include <exception>
#include <mutex>
#include <optional>
#include <stdexcept>

namespace demo_v1 {
    // 固定上限、不覆盖、不隐藏丢帧。错误唤醒所有消费者并保留首次异常。
    template<class T> class Queue {
        std::mutex mutex_;
        std::condition_variable changed_;
        std::deque<T> rows_;
        size_t capacity_, high_ = 0;
        bool closed_ = false;
        std::exception_ptr failure_;
    public:
        explicit Queue(size_t capacity) : capacity_(capacity) {}
        size_t push(T&& row) {
            std::lock_guard<std::mutex> lock(mutex_);
            if (failure_) std::rethrow_exception(failure_);
            if (closed_ || rows_.size() == capacity_) throw std::runtime_error("Bounded queue overflow/closed; no overwrite");
            rows_.push_back(std::move(row));
            high_ = std::max(high_, rows_.size());
            changed_.notify_all();
            return rows_.size();
        }
        // 短时消费者停顿按背压处理；容量不变，超期或首次错误仍停止。
        size_t wait_push(T&& row, std::chrono::milliseconds budget) {
            std::unique_lock<std::mutex> lock(mutex_);
            if (!changed_.wait_for(lock, budget, [&] { return failure_ || closed_ || rows_.size() < capacity_; }))
                throw std::runtime_error("Bounded queue backpressure deadline exceeded; original retained");
            if (failure_) std::rethrow_exception(failure_);
            if (closed_) throw std::runtime_error("Bounded queue closed; original retained");
            rows_.push_back(std::move(row));
            high_ = std::max(high_, rows_.size());
            changed_.notify_all();
            return rows_.size();
        }
        std::optional<T> pop() {
            std::unique_lock<std::mutex> lock(mutex_);
            changed_.wait(lock, [&] { return failure_ || closed_ || !rows_.empty(); });
            if (failure_) std::rethrow_exception(failure_);
            if (rows_.empty()) return {};
            T row = std::move(rows_.front()); rows_.pop_front();
            changed_.notify_all();
            return row;
        }
        // The SDK owner must service display deadlines while CSI input is idle.
        // A timeout is distinct from a fully drained EOF; first errors still win.
        std::optional<T> pop_for(std::chrono::milliseconds budget, bool& finished) {
            std::unique_lock<std::mutex> lock(mutex_);
            changed_.wait_for(lock,budget,[&]{return failure_ || closed_ || !rows_.empty();});
            if(failure_)std::rethrow_exception(failure_);
            finished=closed_ && rows_.empty();
            if(rows_.empty())return {};
            T row=std::move(rows_.front());rows_.pop_front();changed_.notify_all();return row;
        }
        void check() {
            std::lock_guard<std::mutex> lock(mutex_);
            if (failure_) std::rethrow_exception(failure_);
        }
        void close() {
            std::lock_guard<std::mutex> lock(mutex_);
            closed_ = true; changed_.notify_all();
        }
        void fail(std::exception_ptr e) {
            std::lock_guard<std::mutex> lock(mutex_);
            if (!failure_) failure_ = e;
            closed_ = true; changed_.notify_all();
        }
        size_t high_water() {
            std::lock_guard<std::mutex> lock(mutex_); return high_;
        }
        std::deque<T> drain_for_evidence() {
            std::lock_guard<std::mutex> lock(mutex_);
            std::deque<T> rows; rows.swap(rows_); return rows;
        }
    };
}
