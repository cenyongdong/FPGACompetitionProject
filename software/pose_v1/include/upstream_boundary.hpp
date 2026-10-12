#pragma once
#include <cstdint>
#include <filesystem>
#include <map>
#include <string>
#include <thread>
#include <vector>
namespace pose::upstream {
std::string quoted(const std::string&);
struct Sample {
    std::string point,storage,error;
    int64_t value=0;
    uint64_t waitBegin=0,waitEnd=0,readBegin=0,readEnd=0;
    uint32_t countBefore=0,countAfter=0;
    std::vector<char> bytes;
};
// Opaque owned bytes only. No SDK, operator math or device-pointer dereference.
class Evidence {
    std::thread::id owner_=std::this_thread::get_id();
    uint64_t frame_=0,invocation_=0;bool active_=false,saved_=false;
    std::map<std::string,Sample> current_;
    struct Frame {uint64_t frame,invocation;std::map<std::string,Sample> samples;};
    std::vector<Frame> first_;
    struct Row {uint64_t frame,invocation,hash;Sample metadata;size_t bytes;};
    std::vector<Row> rows_;
    void owner()const;
public:
    void begin(uint64_t frame,uint64_t invocation);
    void record(Sample);
    void save(const std::filesystem::path& fresh);
};
}
