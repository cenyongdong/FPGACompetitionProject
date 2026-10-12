#pragma once
#include <cstdint>
#include <vector>
namespace pose::plddr_position {
constexpr uint64_t prefixBytes=96ULL*1024*1024;
constexpr uint64_t sourceLower=64ULL*1024*1024,sourceUpper=128ULL*1024*1024;
struct Pool {uint64_t start,bytes;};
struct Block {uint64_t start,bytes,identity;};
void validatePool(Pool,const std::vector<Block>& initial);
void validateAllocated(Pool,Block prefix,Block a,Block padding,Block b);
}
