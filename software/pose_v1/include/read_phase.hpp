#pragma once
#include <cstdint>
#include <filesystem>
#include <string>
#include <thread>
#include <vector>
namespace pose::read_phase {
// Owns snapshots only; no SDK, device pointers, index correction or recovery.
class Evidence {
    struct Row {
        uint64_t frame=0,invocation=0,begin=0,end=0,cpu=0,errorTime=0;
        uint64_t readHash=0,cpuHash=0;size_t changed=0;
        bool readDone=false,cpuDone=false;
        std::string before,after,atCPU,error;
    };
    struct Owned {uint64_t invocation;std::vector<char> immediate,beforeCPU;};
    std::thread::id owner_=std::this_thread::get_id();
    std::vector<Row> rows_;std::vector<Owned> first_;
    Owned current_{0,{},{}};bool saved_=false;
    void owner()const;
public:
    void begin(uint64_t frame,uint64_t invocation,uint64_t time,std::string identity);
    void readDone(uint64_t time,std::string identity,const char* bytes,size_t count);
    void beforeCPU(uint64_t time,std::string identity,const char* bytes,size_t count);
    void identityAfterSnapshot(bool cpu,std::string identity);
    void error(uint64_t time,std::string message);
    void save(const std::filesystem::path& fresh);
};
}
