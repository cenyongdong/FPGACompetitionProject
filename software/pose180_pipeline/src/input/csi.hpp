#pragma once
#include "core.hpp"
#include <thread>

namespace pose180_demo {
class Csi {
    Shared& shared_;
    std::thread thread_;
public:
    Csi(Shared&,const std::string& configuration,std::uint64_t session);
    ~Csi();
};
}
