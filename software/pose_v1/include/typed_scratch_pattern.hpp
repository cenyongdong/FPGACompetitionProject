#pragma once
#include "scratch_copy_pattern.hpp"
namespace pose::typed_scratch {
using Pair=pose::scratch::Pair;
using Bytes=pose::scratch::Bytes;
constexpr size_t maximumPattern=100;
Bytes pattern(size_t slot,size_t index);
bool matches(const Pair&,size_t index);
void saveExpected(size_t index,const std::filesystem::path& freshDirectory);
}
