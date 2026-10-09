#pragma once
#include "system_timing.hpp"
namespace pose::bounded_load {
// Post-run ARM reconstruction, never represented as a sampled VPU/IPC buffer.
void saveFrameReferences(const std::vector<pose::measurement::Measurement>&,
    const std::vector<pose::validation::FixtureWindow>&,const std::filesystem::path&);
}
