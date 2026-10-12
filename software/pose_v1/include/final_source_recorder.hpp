#pragma once
#include <cstdint>
#include <filesystem>
#include <functional>
#include <map>
#include <string>
#include <thread>
#include <vector>
namespace pose::final_source {
// SDK-free current-frame ownership. Reader must use the public SDK interface.
class Recorder {
public:
    using Reader=std::function<void(char*,size_t)>;
    void begin(uint64_t frame,uint64_t invocation);
    void source(int64_t op,size_t slot,std::string metadata,std::vector<char> host,Reader);
    void output(int64_t op,size_t slot,std::vector<char> owned);
    void capture(const std::filesystem::path&,const std::string& originalError);
private:
    struct Source {std::string metadata;std::vector<char> host;Reader read;};
    using Key=std::pair<int64_t,size_t>;
    std::map<Key,Source> sources_;
    std::map<Key,std::vector<char>> outputs_;
    std::thread::id owner_=std::this_thread::get_id();
    uint64_t frame_=0,invocation_=0;bool begun_=false,captured_=false;
    void owner() const;
};
}
