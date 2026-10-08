#pragma once
#include "vpu_pipeline_encoder.hpp"
#include <deque>
#include <exception>
#include <memory>
#include <mutex>
#include <stdexcept>

namespace pose::video {
struct FrameQueueStats {uint64_t published=0,overwritten=0,coalesced=0,consumed=0;size_t highWater=0;};
// Only pending completed frames live here. Published frames are immutable.
// The encoding worker retains its own latest frame for repeat sampling.
class ResidentFrameQueue {
    mutable std::mutex mutex_;
    std::deque<std::shared_ptr<const OwnedFrame>> pending_;
    FrameQueueStats stats_;
    std::exception_ptr failure_;
    bool stopped_=false;
public:
    void publish(OwnedFrame frame) {
        if(frame.nv12.size()!=nv12FrameBytes || !frame.generatedNs || !frame.inferenceResult)
            throw std::runtime_error("Invalid completed frame");
        auto owned=std::make_shared<const OwnedFrame>(std::move(frame));
        std::lock_guard<std::mutex> lock(mutex_);
        if(failure_)std::rethrow_exception(failure_);
        if(stopped_)throw std::runtime_error("Publish after stop");
        if(pending_.size()==2){pending_.pop_front();++stats_.overwritten;}
        pending_.push_back(std::move(owned));++stats_.published;
        if(pending_.size()>stats_.highWater)stats_.highWater=pending_.size();
    }
    std::shared_ptr<const OwnedFrame> pop() {
        std::lock_guard<std::mutex> lock(mutex_);
        if(failure_)std::rethrow_exception(failure_);
        if(pending_.empty())return {};
        auto frame=std::move(pending_.front());pending_.pop_front();++stats_.consumed;return frame;
    }
    std::shared_ptr<const OwnedFrame> popLatest() {
        std::lock_guard<std::mutex> lock(mutex_);
        if(failure_)std::rethrow_exception(failure_);
        if(pending_.empty())return {};
        while(pending_.size()>1){pending_.pop_front();++stats_.coalesced;}
        auto frame=std::move(pending_.front());pending_.pop_front();++stats_.consumed;return frame;
    }
    void fail(std::exception_ptr failure) {
        std::lock_guard<std::mutex> lock(mutex_);
        if(!failure_)failure_=failure;
        stopped_=true;
    }
    void stop(){std::lock_guard<std::mutex> lock(mutex_);stopped_=true;}
    void check()const{std::lock_guard<std::mutex> lock(mutex_);if(failure_)std::rethrow_exception(failure_);}
    bool stopped()const{std::lock_guard<std::mutex> lock(mutex_);return stopped_;}
    FrameQueueStats stats()const{std::lock_guard<std::mutex> lock(mutex_);return stats_;}
};
}
