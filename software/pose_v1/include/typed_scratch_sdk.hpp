#pragma once
#include "typed_scratch_pattern.hpp"
#include <memory>
namespace pose::typed_scratch {
struct Writes {std::array<uint64_t,2> begin{},end{};};
class SdkScratch {
    struct Impl;std::unique_ptr<Impl> p_;
public:
    SdkScratch(const std::filesystem::path& graph,const std::filesystem::path& freshEvidence);
    ~SdkScratch();
    void readSources(Pair& callerOwned);
    void writePattern(size_t index,Writes& callerOwned);
    void copyPair(Pair& callerOwned);
};
}
