#pragma once
#include "scratch_copy_pattern.hpp"
#include <memory>
namespace pose::scratch {
class SdkScratch {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    explicit SdkScratch(const std::filesystem::path& freshEvidence);
    ~SdkScratch();
    Pair readSources();
    Pair copyPair();
};
}
