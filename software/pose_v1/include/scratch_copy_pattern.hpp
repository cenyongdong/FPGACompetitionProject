#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <vector>
namespace pose::scratch {
constexpr size_t pairLimit=100;
constexpr std::array<size_t,2> sizes{30240,16800};
using Bytes=std::vector<char>;
struct Pair {std::array<Bytes,2> values;std::array<uint64_t,2> copyBegin{},copyEnd{},shadowBegin{},shadowEnd{};};
Bytes pattern(size_t slot);
Bytes own(const char* pointer,size_t bytes);
uint64_t fingerprint(const Bytes&);
bool matches(const Pair&);
void savePair(const Pair&,const std::filesystem::path& freshDirectory);
}
