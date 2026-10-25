#pragma once
#include <array>
#include <chrono>
#include <condition_variable>
#include <exception>
#include <memory>
#include <mutex>
#include <optional>
#include <stdexcept>

namespace pose180_pipeline {
// Slots stay at fixed addresses. A lease is their sole owner; only complete
// values enter the ready ring. No pointer into SDK-owned memory is queued.
template<class T, std::size_t N> class FixedPool {
    struct Slot { T value{}; unsigned state=0; };
    std::unique_ptr<std::array<Slot,N>> slots_=std::make_unique<std::array<Slot,N>>();
    std::array<std::size_t,N> ready_{};
    std::size_t head_=0, count_=0, high_=0;
    bool closed_=false;
    std::exception_ptr error_;
    mutable std::mutex mutex_;
    std::condition_variable changed_;
    void release(std::size_t i) noexcept {
        std::lock_guard<std::mutex> lock(mutex_);(*slots_)[i].state=0;changed_.notify_all();
    }
public:
    class Lease {
        FixedPool* pool_=nullptr;std::size_t index_=0;
        friend class FixedPool;
        Lease(FixedPool* p,std::size_t i):pool_(p),index_(i){}
    public:
        Lease()=default;Lease(const Lease&)=delete;Lease& operator=(const Lease&)=delete;
        Lease(Lease&& other) noexcept:pool_(other.pool_),index_(other.index_){other.pool_=nullptr;}
        Lease& operator=(Lease&& other) noexcept {
            if(this!=&other){if(pool_)pool_->release(index_);pool_=other.pool_;index_=other.index_;other.pool_=nullptr;}return *this;
        }
        ~Lease(){if(pool_)pool_->release(index_);}
        T& value(){if(!pool_)throw std::logic_error("Empty pool lease");return (*pool_->slots_)[index_].value;}
    };
    Lease acquire(std::chrono::milliseconds budget) {
        std::unique_lock<std::mutex> lock(mutex_);
        auto free_slot=[&]{for(const auto& s:*slots_)if(s.state==0)return true;return false;};
        if(!changed_.wait_for(lock,budget,[&]{return error_||closed_||free_slot();}))
            throw std::runtime_error("Fixed input/result pool backpressure deadline");
        if(error_)std::rethrow_exception(error_);
        if(closed_)throw std::runtime_error("Pool closed");
        for(std::size_t i=0;i<N;++i)if((*slots_)[i].state==0){(*slots_)[i].state=1;return Lease(this,i);}
        throw std::logic_error("Pool free-slot invariant");
    }
    void publish(Lease&& lease) {
        std::lock_guard<std::mutex> lock(mutex_);
        if(error_)std::rethrow_exception(error_);
        if(closed_||lease.pool_!=this||count_==N||(*slots_)[lease.index_].state!=1)
            throw std::logic_error("Invalid pool publication");
        (*slots_)[lease.index_].state=2;ready_[(head_+count_)%N]=lease.index_;++count_;
        if(count_>high_)high_=count_;
        lease.pool_=nullptr;changed_.notify_all();
    }
    std::optional<Lease> pop(std::chrono::milliseconds budget,bool& eof) {
        std::unique_lock<std::mutex> lock(mutex_);
        changed_.wait_for(lock,budget,[&]{return error_||closed_||count_;});
        if(error_)std::rethrow_exception(error_);
        eof=closed_&&!count_;
        if(!count_)return {};
        auto i=ready_[head_];head_=(head_+1)%N;--count_;(*slots_)[i].state=3;
        changed_.notify_all();return Lease(this,i);
    }
    void close(){std::lock_guard<std::mutex> lock(mutex_);closed_=true;changed_.notify_all();}
    void fail(std::exception_ptr e){std::lock_guard<std::mutex> lock(mutex_);if(!error_)error_=e;closed_=true;changed_.notify_all();}
    void check(){std::lock_guard<std::mutex> lock(mutex_);if(error_)std::rethrow_exception(error_);}
    std::size_t high_water()const{std::lock_guard<std::mutex> lock(mutex_);return high_;}
    // Called after producer/consumer joins. Retain completed unpublished results.
    template<class Save> void save_queued(Save&& save){for(const auto& s:*slots_)if(s.state==2)save(s.value);}
};
}
