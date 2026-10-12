#pragma once
#include "tcp_receiver.hpp"
#include <filesystem>

namespace pose::measurement {
// Exposes complete arrival stamps without adding SDK or oracle dependencies.
class TimedWindowInput {
    pose_v1::transport::Receiver receiver_;
    size_t consumed_=0,returned_=0;std::filesystem::path evidence_;bool saved_=false;
    void saveStats(bool failure);
public:
    explicit TimedWindowInput(const std::filesystem::path&);
    ~TimedWindowInput();
    void markReturned(){++returned_;}
    std::optional<pose_v1::transport::Item> next();
    void finish(const std::filesystem::path&,bool requireAll,size_t expected=33);
};
}
