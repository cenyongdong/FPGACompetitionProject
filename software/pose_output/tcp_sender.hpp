#pragma once
#include "pose_frame.hpp"
#include <memory>
#include <string>

namespace pose::output {
    // 同步有界发送器，由输出工作线程持有；不得在推理线程等待网络。
    // 失败不重连，不重复提交。构造和每条记录均有独立超时。
    class TcpSender {
    public:
        TcpSender(const std::string& ipv4, std::uint16_t port, unsigned timeout_ms = 2000);
        ~TcpSender();
        TcpSender(const TcpSender&) = delete;
        TcpSender& operator=(const TcpSender&) = delete;
        void send(const Frame&, unsigned fragment_bytes = record_bytes);
    private:
        struct Impl;
        std::unique_ptr<Impl> impl_;
    };
}
