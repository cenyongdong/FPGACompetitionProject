#include "host_failure_evidence.hpp"
#include <fstream>
#include <iomanip>
#include <mutex>
#include <stdexcept>
#include <limits>
namespace pose::failure_evidence {
namespace {
std::mutex mutex;
std::filesystem::path directory;
bool active=false,consumed=false;
void need(bool yes,const char* reason){if(!yes)throw std::runtime_error(reason);}
std::string quote(const std::string& s){
    std::string out="\"";const char* hex="0123456789abcdef";
    for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=c;}
        else if(c<32){out+="\\u00";out+=hex[c>>4];out+=hex[c&15];}else out+=c;}
    return out+'"';
}
}
void configure(const std::filesystem::path& output){
    std::lock_guard<std::mutex> g(mutex);need(!active&&!output.empty()&&!std::filesystem::exists(output),"Preserve failure evidence");
    directory=output;active=true; // No directory or IO on the successful path.
}
bool enabled(){std::lock_guard<std::mutex> g(mutex);return active;}
void save(uint64_t frame,uint64_t invocation,int64_t op,const std::string& error,const std::vector<Blob>& inputs,const std::string& declarations){
    std::lock_guard<std::mutex> g(mutex);need(active&&!consumed&&!std::filesystem::exists(directory),"Only one fresh failure capture");
    need(!inputs.empty()&&inputs.size()<=4,"Failure capture arity bound");
    size_t total=0;
    for(size_t i=0;i<inputs.size();++i){const auto& v=inputs[i];need(v.slot==i&&!v.bytes.empty()&&v.bytes.size()%4==0,"Failure input slot/FP32 size");
        need(v.offset<=v.chunkBytes&&v.bytes.size()<=v.chunkBytes-v.offset,"Failure input bounds");
        size_t elements=1;need(!v.shape.empty()&&v.shape.size()<=5,"Failure shape rank");
        for(int64_t d:v.shape){need(d>0&&uint64_t(d)<=std::numeric_limits<size_t>::max()/elements,"Failure shape overflow");elements*=size_t(d);}
        need(elements<=262144&&elements*4==v.bytes.size(),"Failure shape bytes");
        total+=v.bytes.size();need(total<=1024*1024,"Failure aggregate byte limit");
    }
    consumed=true;std::filesystem::create_directory(directory);
    std::ofstream index(directory/"failure.json");need(bool(index),"Failure index open");
    index<<"{\"status\":\"captured_after_CPU_exception\",\"frame_id\":"<<frame<<",\"invocation\":"<<invocation<<",\"op_id\":"<<op<<",\"error\":"<<quote(error)<<",\"device_read\":false,\"input_phase\":\"owned_Host_staging_after_kernel_exception\",\"declarations\":"<<declarations<<",\"inputs\":[";
    for(size_t i=0;i<inputs.size();++i){const auto& v=inputs[i];const auto name="input"+std::to_string(i)+".f32";
        std::ofstream f(directory/name,std::ios::binary);f.write(v.bytes.data(),std::streamsize(v.bytes.size()));f.close();need(bool(f),"Failure input write");
        if(i){index<<',';}
        index<<"{\"slot\":"<<i<<",\"file\":"<<quote(name)<<",\"bytes\":"<<v.bytes.size()<<",\"pointer\":\"CPTR\",\"dtype\":\"FP32\",\"layout\":"<<quote(v.layout)<<",\"merged_distributions\":"<<v.distributions<<",\"offset\":"<<v.offset<<",\"chunk_bytes\":"<<v.chunkBytes<<",\"shape\":[";
        for(size_t j=0;j<v.shape.size();++j){if(j)index<<',';index<<v.shape[j];}index<<"]}";
    }
    index<<"]}\n";index.close();need(bool(index),"Failure index write");
}
void noteCaptureError(const std::string& error) noexcept{
    try{std::lock_guard<std::mutex> g(mutex);if(!active)return;
        if(!std::filesystem::exists(directory))std::filesystem::create_directory(directory);
        std::ofstream f(directory/"capture-error.txt");f<<error<<'\n';
    }catch(...){}
}
}
