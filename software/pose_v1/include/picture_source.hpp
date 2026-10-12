#pragma once
#include "resident_frame_queue.hpp"
#include "vpu_resident_encoder.hpp"
#include <thread>
namespace pose::picture {
// Value-only source: producer owns publication, encoder owns sampling/repeats.
class Source {
    const std::thread::id producer_=std::this_thread::get_id();
    std::optional<std::thread::id> consumer_;
    pose::video::ResidentFrameQueue queue_;
    std::shared_ptr<const pose::video::OwnedFrame> latest_;
    uint64_t next_=0,previous_=0;bool previousReal_=false;
public:
    explicit Source(pose::video::OwnedFrame warmup);
    void publish(pose::video::OwnedFrame);
    std::optional<pose::video::ResidentSample> sample(unsigned,uint64_t);
    void stop();
    void fail(std::exception_ptr);
    void check()const;
    pose::video::FrameQueueStats stats()const;
};
void markEncodedId(std::vector<uint8_t>&,unsigned);
std::string frameHash(const std::vector<uint8_t>&);
}
