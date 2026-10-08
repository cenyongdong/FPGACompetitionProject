#pragma once
#include "display_protocol.hpp"
#include <condition_variable>
#include <deque>
#include <exception>
#include <memory>
#include <mutex>
#include <stdexcept>

namespace pose::display {
struct QueueStats {uint64_t published=0,adopted=0,overwritten=0,coalesced=0;size_t highWater=0;};
class Queue {
    mutable std::mutex mutex_;std::condition_variable cv_;
    std::deque<std::shared_ptr<const Pose>> pending_;QueueStats stats_;
    bool closed_=false;std::exception_ptr failure_;
public:
    void publish(Pose pose){
        validate(pose);auto value=std::make_shared<const Pose>(std::move(pose));std::lock_guard<std::mutex> lock(mutex_);
        if(failure_)std::rethrow_exception(failure_);
        if(closed_)throw std::runtime_error("Display publish after close");
        if(pending_.size()==2){pending_.pop_front();++stats_.overwritten;}pending_.push_back(std::move(value));++stats_.published;
        if(pending_.size()>stats_.highWater)stats_.highWater=pending_.size();
        cv_.notify_one();
    }
    std::shared_ptr<const Pose> next(){
        std::unique_lock<std::mutex> lock(mutex_);cv_.wait(lock,[&]{return failure_||closed_||!pending_.empty();});
        if(failure_)std::rethrow_exception(failure_);
        if(pending_.empty())return {};
        while(pending_.size()>1){pending_.pop_front();++stats_.coalesced;}auto p=std::move(pending_.front());pending_.pop_front();++stats_.adopted;return p;
    }
    void close(){std::lock_guard<std::mutex> lock(mutex_);closed_=true;cv_.notify_all();}
    void fail(std::exception_ptr e){std::lock_guard<std::mutex> lock(mutex_);failure_=e;closed_=true;cv_.notify_all();}
    QueueStats stats()const{std::lock_guard<std::mutex> lock(mutex_);return stats_;}
};
}
