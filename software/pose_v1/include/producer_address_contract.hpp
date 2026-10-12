#pragma once
#include <cstdint>
#include <vector>
namespace pose::producer_address {
inline constexpr uint64_t prefixBytes=104ULL*1024*1024;
inline constexpr uint64_t lower=prefixBytes,upper=105ULL*1024*1024;
struct Pool {uint64_t start,bytes;};
struct Block {uint64_t start,bytes,identity;};
void validatePool(Pool,const std::vector<Block>&);
void validatePrefix(Pool,Block);
void validateMap(Pool,Block,const std::vector<Block>&);
void validateBoundary(Block);
}
