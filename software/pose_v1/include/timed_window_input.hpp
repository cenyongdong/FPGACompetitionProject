#pragma once
#include "tcp_receiver.hpp"
#include <filesystem>

namespace pose::measurement {
// Exposes complete arrival stamps without adding SDK or oracle dependencies.
class TimedWindowInput {
    pose_v1::transport::Receiver receiver_;
    size_t consumed_=0;
public:
    TimedWindowInput();
    std::optional<pose_v1::transport::Item> next();
    void finish(const std::filesystem::path&,bool requireAll);
};
}
