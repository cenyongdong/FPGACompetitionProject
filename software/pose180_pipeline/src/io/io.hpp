#pragma once
#include "core.hpp"
#include <thread>

namespace pose180_demo {
// Three independent nonblocking sockets; no archive ACK in demo mode.
class Io {
    Shared& shared_;
    std::thread thread_;
public:
    Io(Shared&, const std::string& bind, unsigned input_port, unsigned result_port,
       unsigned status_port, std::uint64_t session, bool mock, bool hdmi,unsigned view_port=0);
    ~Io();
    Io(const Io&)=delete;
};
}
