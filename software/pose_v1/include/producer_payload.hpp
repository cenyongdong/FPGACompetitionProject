#pragma once
#include <array>
#include <cstdint>
#include <filesystem>
#include <string>
#include <vector>
namespace pose::producer {
using Bytes=std::vector<char>;
using Pair=std::array<Bytes,2>;
struct Payload {Pair inputs,expected;};
inline constexpr std::array<int64_t,2> inputIds{486,478},outputIds{4386,4390};
inline constexpr std::array<size_t,2> inputSizes{400,17280},outputSizes{30240,16800};
void need(bool condition,const char* message);
Bytes readFile(const std::filesystem::path&,size_t exactBytes);
void saveFile(const std::filesystem::path&,const Bytes&);
void validate(const Payload&);
Payload load(const std::filesystem::path&);
void compareSaved(const std::filesystem::path&,const Payload&);
uint64_t fingerprint(const Bytes&);
std::string text(const std::filesystem::path&);
void saveText(const std::filesystem::path&,const std::string&);
}
