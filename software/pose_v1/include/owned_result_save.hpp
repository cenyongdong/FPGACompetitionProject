#pragma once
#include "system_timing.hpp"
namespace pose::owned_results {
void saveReturned(const pose::measurement::Measurement&,size_t,const std::filesystem::path&);
// Serialization only: writes every returned value, including rejected/nonfinite values.
void save(const std::vector<pose::measurement::Measurement>&,const std::vector<pose::validation::FixtureWindow>&,const std::filesystem::path&);
}
