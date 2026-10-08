#pragma once
#include "tcp_receiver.hpp"
#include <filesystem>
#include <fstream>

namespace pose::input {
// Owns only the complete-window receiver and its transport evidence.
// It has no model, reference data, rendering or encoder dependencies.
class TcpWindowInput {
    pose_v1::transport::Receiver receiver_;
    std::ofstream log_;
    std::filesystem::path evidence_;
    size_t consumed_=0;
public:
    explicit TcpWindowInput(const std::filesystem::path& evidence);
    pose_v1::Window next();
    void finish(size_t expected);
};
}
