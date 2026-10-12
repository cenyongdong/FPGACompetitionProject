#include "host_stage_observation.hpp"
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <mutex>
#include <stdexcept>
#include <thread>
namespace pose::stage_observation {
namespace {
std::filesystem::path root;bool configured=false;std::mutex mutex;std::vector<std::string> rows;
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
std::string jsonString(const char* text){std::ostringstream s;s<<'"';for(const unsigned char c:std::string(text)){switch(c){case '"':s<<"\\\"";break;case '\\':s<<"\\\\";break;case '\n':s<<"\\n";break;case '\r':s<<"\\r";break;case '\t':s<<"\\t";break;default:if(c<32)s<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;else s<<c;}}s<<'"';return s.str();}
void append(std::string row){std::lock_guard<std::mutex> lock(mutex);need(rows.size()<2048,"Stage metadata budget exceeded");rows.push_back(std::move(row));}
void fields(std::ostream& s,const Info& i){s<<"\"slot\":"<<i.slot<<",\"bytes\":"<<i.bytes<<",\"source_kind\":"<<std::quoted(i.sourceKind)<<",\"source_region\":"<<std::quoted(i.sourceRegion)<<",\"source_address\":"<<i.sourceAddress<<",\"source_offset\":"<<i.sourceOffset<<",\"source_capacity\":"<<i.sourceCapacity<<",\"Host_region\":"<<std::quoted(i.hostRegion)<<",\"Host_CPTR\":"<<i.hostPointer<<",\"Host_chunk\":"<<i.hostChunk<<",\"Host_offset\":"<<i.hostOffset<<",\"Host_capacity\":"<<i.hostCapacity<<",\"mod64\":"<<i.hostPointer%64<<",\"mod128\":"<<i.hostPointer%128<<",\"mod256\":"<<i.hostPointer%256<<",\"wait_begin_ns\":"<<i.waitBegin<<",\"wait_end_ns\":"<<i.waitEnd<<",\"copy_begin_ns\":"<<i.copyBegin<<",\"copy_end_ns\":"<<i.copyEnd;}
}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
Completion waitFresh(uint32_t target,uint32_t maximum,const std::function<uint32_t()>& read,std::chrono::milliseconds timeout){
    need(target>0&&target<=maximum&&bool(read)&&timeout.count()>=0&&timeout.count()<=10000,"Invalid completion wait contract");Completion r;r.target=target;r.begin=now();uint32_t previous=0;
    while(true){const auto count=read();if(!r.polls)r.initial=count;need(count<=maximum&&(!r.polls||count>=previous),"Completion count range/regression");previous=count;r.final=count;++r.polls;
        if(count>=target){r.end=now();return r;}
        need(now()-r.begin<uint64_t(timeout.count())*1000000ULL,"Explicit completion wait timeout");std::this_thread::yield();}
}
void configure(const std::filesystem::path& path){std::lock_guard<std::mutex> lock(mutex);need(!configured&&!path.empty()&&!std::filesystem::exists(path),"Preserve stage observations");root=path;configured=true;}
std::filesystem::path failureRoot(){need(configured,"Stage observation is not configured");return root.parent_path()/"failed-host-inputs";}
void saveMetadata(){std::lock_guard<std::mutex> lock(mutex);if(!configured)return;need(!std::filesystem::exists(root),"Preserve stage observations");std::filesystem::create_directory(root);std::ofstream f(root/"metadata.jsonl");for(const auto& r:rows)f<<r<<'\n';f.close();need(bool(f),"Stage metadata save failed");}
void recordCompletion(uint64_t frame,uint64_t invocation,int64_t op,const Completion& r){if(!configured)return;std::ostringstream s;s<<"{\"kind\":\"fresh_group_completion\",\"frame_id\":"<<frame<<",\"invocation\":"<<invocation<<",\"op_id\":"<<op<<",\"target\":"<<r.target<<",\"initial\":"<<r.initial<<",\"final\":"<<r.final<<",\"polls\":"<<r.polls<<",\"begin_ns\":"<<r.begin<<",\"end_ns\":"<<r.end<<",\"DMA_cache_fence_proven\":false}";append(s.str());}
void recordSyncFailure(uint64_t frame,uint64_t invocation,int64_t op,const char* error){if(!configured)return;std::ostringstream s;s<<"{\"kind\":\"completion_wait_failed\",\"frame_id\":"<<frame<<",\"invocation\":"<<invocation<<",\"op_id\":"<<op<<",\"error\":"<<jsonString(error)<<"}";append(s.str());}
void Call::afterCopy(Info info,const char* pointer){if(!configured)return;need(entries_.size()<4&&pointer&&info.bytes>0&&info.bytes<=1024*1024&&total_<=1024*1024-info.bytes,"Shadow arity/byte bound");
    need(info.hostPointer==reinterpret_cast<uintptr_t>(pointer),"Shadow pointer identity differs");Entry e{std::move(info),now(),0,{}};e.bytes.resize(e.info.bytes);std::memcpy(e.bytes.data(),pointer,e.bytes.size());e.end=now();total_+=e.bytes.size();
    std::ostringstream s;s<<"{\"kind\":\"post_copy_Host_shadow\",\"frame_id\":"<<frame_<<",\"invocation\":"<<invocation_<<",\"op_id\":"<<op_<<',';fields(s,e.info);s<<",\"shadow_begin_ns\":"<<e.begin<<",\"shadow_end_ns\":"<<e.end<<"}";append(s.str());entries_.push_back(std::move(e));}
void Call::validate()const{for(size_t i=0;i<entries_.size();++i){const auto& a=entries_[i].info;
    need(a.hostPointer&&a.hostPointer%alignof(float)==0&&a.bytes%sizeof(float)==0,"Host staging FP32 alignment differs");
    need(a.hostOffset<=a.hostCapacity&&a.bytes<=a.hostCapacity-a.hostOffset,"Host staging capacity differs");
    need(a.sourceOffset<=a.sourceCapacity&&a.bytes<=a.sourceCapacity-a.sourceOffset,"Source staging capacity differs");
    need(a.sourceKind=="CPTR"||a.sourceAddress%alignof(float)==0,"Device source FP32 address alignment differs");
    need(a.hostPointer<=UINT64_MAX-a.bytes,"Host address span overflow");
    for(size_t j=0;j<i;++j){const auto& b=entries_[j].info;need(a.hostPointer+a.bytes<=b.hostPointer||b.hostPointer+b.bytes<=a.hostPointer,"New Host staging buffers overlap");}}
}
void Call::saveFailure(const std::filesystem::path& parent,uint64_t errorTime)const{if(!configured)return;need(!entries_.empty()&&std::filesystem::is_directory(parent),"Shadow must follow saved Host error");const auto dir=parent/"post-copy";need(!std::filesystem::exists(dir),"Preserve shadow failure");std::filesystem::create_directory(dir);std::ofstream index(dir/"shadow.json");
    index<<"{\"frame_id\":"<<frame_<<",\"invocation\":"<<invocation_<<",\"op_id\":"<<op_<<",\"error_ns\":"<<errorTime<<",\"original_copy_math_unchanged\":true,\"inputs\":[";
    for(size_t i=0;i<entries_.size();++i){const auto& e=entries_[i];std::ofstream f(dir/("input"+std::to_string(e.info.slot)+".f32"),std::ios::binary);f.write(e.bytes.data(),e.bytes.size());f.close();need(bool(f),"Shadow byte save failed");if(i)index<<',';index<<'{';fields(index,e.info);index<<",\"shadow_begin_ns\":"<<e.begin<<",\"shadow_end_ns\":"<<e.end<<'}';}index<<"]}\n";index.close();need(bool(index),"Shadow index save failed");}
}
