#pragma once
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <vector>
#include <stdexcept>

namespace pose_v1::forward_clock {
using Clock=std::chrono::steady_clock;
struct Record { const char* kind;int64_t op,slot;uint64_t frame,invocation;int64_t begin,end; };
inline std::mutex mutex;
inline bool active=false,overflow=false;
inline size_t sample_limit=4;
inline constexpr size_t record_limit=8192;
inline Clock::time_point epoch;
inline uint64_t frame=0,invocation=0;
inline std::vector<Record> records;
inline void start(uint64_t f,uint64_t i,Clock::time_point t) {
    std::lock_guard<std::mutex> guard(mutex);
    if(records.empty())records.reserve(record_limit);
    frame=f;invocation=i;epoch=t;active=i<sample_limit;
}
inline void record(const char* kind,int64_t op,int64_t slot,Clock::time_point a,Clock::time_point b) {
    std::lock_guard<std::mutex> guard(mutex);if(!active)return;
    if(records.size()>=record_limit){overflow=true;return;}
    auto ns=[](auto t){return std::chrono::duration_cast<std::chrono::nanoseconds>(t-epoch).count();};
    records.push_back({kind,op,slot,frame,invocation,ns(a),ns(b)});
}
class Span {
    const char* kind_;int64_t op_,slot_;Clock::time_point begin_;
public:
    Span(const char* k,int64_t o=0,int64_t s=0):kind_(k),op_(o),slot_(s),begin_(Clock::now()){}
    ~Span(){record(kind_,op_,slot_,begin_,Clock::now());}
};
inline void save(const std::filesystem::path& path) {
    std::lock_guard<std::mutex> guard(mutex);std::ofstream out(path);
    if(!out)throw std::runtime_error("Cannot save monotonic timing evidence");
    if(overflow)throw std::runtime_error("Diagnostic timing capacity exceeded");
    for(const auto& r:records)out<<"{\"kind\":\""<<r.kind<<"\",\"op_id\":"<<r.op<<",\"slot\":"<<r.slot
        <<",\"frame_id\":"<<r.frame<<",\"invocation\":"<<r.invocation<<",\"begin_ns\":"<<r.begin<<",\"end_ns\":"<<r.end<<"}\n";
    if(!out)throw std::runtime_error("Monotonic timing evidence write failed");
}
}
