#pragma once
#include "core.hpp"
#include <filesystem>
#include <thread>

namespace pose180_demo {
// Finite local PIWCSI2 input. No network, SDK, model or preprocessing changes.
class Dataset {
    Shared& shared_;
    std::thread thread_;
public:
    Dataset(Shared&, const std::filesystem::path&, std::uint64_t session, unsigned repetitions=1);
    ~Dataset();
    Dataset(const Dataset&)=delete;
};
}
