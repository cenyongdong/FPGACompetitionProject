#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <cmath>

// Comparison only: owned Host TopK indices, before their existing writeback.
// The frozen graph casts integer [0,179] through FP16, multiplies by 42 ones,
// then removes six padded channels. These integers are represented exactly.
namespace pose_v1::mixed_candidate::index_oracle {
struct Sample {uint64_t invocation; std::array<float,100> topk;};
inline std::deque<Sample> recent;
inline uint64_t checked=0, mismatches=0;
inline void remember(uint64_t invocation, const char* host, size_t bytes) {
    if (!host || bytes != 400) throw std::runtime_error("Host TopK oracle shape differs");
    Sample s{invocation,{}}; std::memcpy(s.topk.data(),host,400);
    for (float v:s.topk) if (!std::isfinite(v)||v<0||v>=180||std::trunc(v)!=v)
        throw std::runtime_error("Host TopK oracle index invalid");
    if (recent.size()==8) recent.pop_front();
    recent.push_back(s);
}
inline void check(uint64_t invocation, const char* original, size_t bytes) {
    if (recent.empty()||recent.back().invocation!=invocation||!original||bytes!=16800)
        throw std::runtime_error("Host TopK oracle invocation/shape differs");
    size_t different=0;
    for(size_t i=0;i<4200;++i) if(std::memcmp(original+i*4,&recent.back().topk[i/42],4)) ++different;
    ++checked;
    if(different) {++mismatches;throw std::runtime_error("First op192 read differs from owned Host TopK oracle: "+std::to_string(different)+" words");}
}
inline void save(const std::filesystem::path& root) {
    if(std::filesystem::exists(root)) throw std::runtime_error("Preserve index oracle evidence");
    std::filesystem::create_directory(root);
    std::ofstream index(root/"summary.json");
    index<<"{\"checked\":"<<checked<<",\"mismatches\":"<<mismatches<<",\"comparison_only\":true,\"recent\":[";
    bool first=true;
    for(const auto& s:recent) {
        if(!first)index<<','; first=false;
        index<<s.invocation;
        std::ofstream f(root/(std::to_string(s.invocation)+".topk.f32"),std::ios::binary);
        f.write(reinterpret_cast<const char*>(s.topk.data()),400);f.close();
        if(!f)throw std::runtime_error("Host TopK oracle save failed");
    }
    index<<"]}\n";index.close();if(!index)throw std::runtime_error("Host TopK oracle summary failed");
}
}
