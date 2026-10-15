#pragma once
#include <icraft-xrt/core/session.h>
#include <filesystem>
#include <fstream>
#include <stdexcept>
namespace pose_v1::timing_sdk {
    inline bool enabled = false;
    inline void configure(bool on) { if(on) throw std::runtime_error("Unverified SDK profiling disabled"); }
    inline void collect(const icraft::xrt::Session&,const icraft::xrt::Device&) {}
    inline void save(const std::filesystem::path& p) {
        std::ofstream(p/"sdk-profile.jsonl"); std::ofstream(p/"hardware-layers.jsonl");
    }
}
