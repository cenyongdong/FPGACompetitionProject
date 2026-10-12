#pragma once
#include <cstdint>
#include <cstddef>
#include <filesystem>
#include <functional>
#include <string>
#include <thread>
#include <vector>
namespace pose::producer_count {
enum class Point { BeforeWait, AfterWait, BeforeCopy, AfterCopy };
struct Source {
    int64_t producer=0;
    uint64_t address=0,offset=0,capacity=0,bytes=0;
    std::string kind,region;
};
class Recorder {
    struct Row {uint64_t frame,invocation,begin,end;size_t slot;Point point;Source source;uint32_t count=0;bool completed=false;std::string error;};
    std::thread::id owner_=std::this_thread::get_id();
    bool active_=false,failed_=false;uint64_t frame_=0,invocation_=0;size_t next_=0;
    uint32_t previous_=0;Source sources_[2];std::vector<Row> rows_;
public:
    void sample(uint64_t frame,uint64_t invocation,size_t slot,Point,const Source&,const std::function<uint32_t()>&);
    void save(const std::filesystem::path& freshDirectory)const;
    size_t size()const{return rows_.size();}
};
void configure(const std::filesystem::path& freshDirectory);
void sample(uint64_t frame,uint64_t invocation,size_t slot,Point,const Source&,const std::function<uint32_t()>&);
void save();
}
