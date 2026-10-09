#include "failure_source_readback.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <chrono>
#include <fstream>
#include <mutex>
#include <sstream>
#include <iomanip>
#include <stdexcept>
namespace pose::source_diagnostic {
namespace {
namespace xrt=icraft::xrt;
std::mutex mutex;
std::filesystem::path directory;
bool configured=false,consumed=false;
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
std::string quote(const std::string& s){std::string out="\"";const char* h="0123456789abcdef";
    for(unsigned char c:s){if(c=='"'||c=='\\'){out+='\\';out+=c;}
        else if(c<32){out+="\\u00";out+=h[c>>4];out+=h[c&15];}else out+=c;}
    return out+'"';
}
struct Info {std::string kind,region,chunk;bool device=false;uint64_t address=0,cptr=0,offset=0,capacity=0;size_t bytes=0;std::vector<int64_t> shape;};
struct Owned {std::vector<char> bytes;uint64_t begin=0,end=0;};
void fields(std::ostream& out,const Info& i,size_t slot){
    out<<"{\"slot\":"<<slot<<",\"pointer\":"<<quote(i.kind)<<",\"device\":"<<(i.device?"true":"false")<<",\"region\":"<<quote(i.region)<<",\"chunk_identity\":"<<quote(i.chunk)<<",\"address\":"<<i.address<<",\"CPTR_metadata\":"<<i.cptr<<",\"offset\":"<<i.offset<<",\"chunk_bytes\":"<<i.capacity<<",\"bytes\":"<<i.bytes<<",\"shape\":[";
    for(size_t j=0;j<i.shape.size();++j){if(j){out<<',';}out<<i.shape[j];}out<<']';
}
}
void configure(const std::filesystem::path& output){std::lock_guard<std::mutex> g(mutex);
    need(!configured&&!output.empty()&&!std::filesystem::exists(output),"Preserve source readback directory");directory=output;configured=true;
}
void capture(uint64_t frame,uint64_t invocation,int64_t op,const std::vector<icraft::xrt::Tensor>& sources,const icraft::xrt::Device& expected,bool permit,size_t stagingBytes){
    std::lock_guard<std::mutex> g(mutex);
    need(configured&&!consumed&&!std::filesystem::exists(directory)&&std::filesystem::is_directory(directory.parent_path()),"Source readback must follow saved Host failure");
    need(!sources.empty()&&sources.size()<=4&&stagingBytes>0&&stagingBytes<=1024*1024,"Source capture arity/size bound");
    std::vector<Info> info;size_t total=0;
    for(const auto& t:sources){
        need(t.hasData()&&t.dtype()->element_dtype.isFP32(),"Source must be allocated FP32");
        const auto bytes=t.dtype().bytes();need(bytes>0&&bytes<=1024*1024,"Source declaration byte bound");
        need(t.offset()<=t.chunk()->byte_size&&uint64_t(bytes)<=t.chunk()->byte_size-t.offset(),"Source storage bounds");
        const auto ptr=t.data();Info i;const auto kind=ptr.ptype();
        need(kind==xrt::PtrType::CPTR||kind==xrt::PtrType::ADDR||kind==xrt::PtrType::BOTH,"Source pointer kind");
        const bool host=t.isOn(xrt::HostDevice::MemRegion());
        if(!host)need(permit&&expected.defined()&&t.memRegion().device().same_as(expected),"Source belongs to unexpected device");
        if(host)need(kind==xrt::PtrType::CPTR,"Host source must be CPTR");
        i.kind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";
        // Public pointer metadata only. ADDR/BOTH is never dereferenced here.
        if(kind!=xrt::PtrType::CPTR)i.address=ptr.addr();
        if(kind!=xrt::PtrType::ADDR)i.cptr=reinterpret_cast<uintptr_t>(ptr.cptr());
        i.region=std::string(t.memRegion()->typeKey());i.device=!host;
        std::ostringstream identity;identity<<static_cast<const void*>(t.chunk().operator->());i.chunk=identity.str();
        i.offset=t.offset();i.capacity=t.chunk()->byte_size;i.bytes=size_t(bytes);
        for(int64_t d:t.dtype()->shape)i.shape.push_back(d);
        total+=i.bytes;need(total<=stagingBytes,"Source aggregate exceeds saved staging");info.push_back(std::move(i));
    }
    need(total==stagingBytes,"Source/staging byte coverage differs");consumed=true;
    std::filesystem::create_directory(directory);
    std::ofstream started(directory/"started.json");started<<"{\"frame_id\":"<<frame<<",\"invocation\":"<<invocation<<",\"op_id\":"<<op<<",\"rounds\":2,\"single_round_bytes\":"<<total<<",\"normal_forward_changed\":false,\"sources\":[";
    for(size_t j=0;j<info.size();++j){if(j){started<<',';}fields(started,info[j],j);started<<'}';}started<<"]}\n";
    started.close();need(bool(started),"Source start record failed");
    std::vector<Owned> owned(2*sources.size());
    try{
        // Own all buffers before read one. No file writes between the two rounds.
        for(size_t round=0;round<2;++round)for(size_t slot=0;slot<sources.size();++slot)owned[round*sources.size()+slot].bytes.resize(info[slot].bytes);
        for(size_t round=0;round<2;++round)for(size_t slot=0;slot<sources.size();++slot){auto& item=owned[round*sources.size()+slot];
            item.begin=now();sources[slot].read(item.bytes.data(),0,info[slot].bytes);item.end=now();
        }
    }catch(...){
        // Preserve any completed reads; caller preserves the original CPU error.
        for(size_t j=0;j<owned.size();++j)if(owned[j].end){std::ofstream f(directory/("partial"+std::to_string(j)+".f32"),std::ios::binary);f.write(owned[j].bytes.data(),std::streamsize(owned[j].bytes.size()));}
        throw;
    }
    std::ofstream index(directory/"readback.json");need(bool(index),"Source index open");
    index<<"{\"status\":\"two_SDK_source_reads_completed\",\"frame_id\":"<<frame<<",\"invocation\":"<<invocation<<",\"op_id\":"<<op<<",\"method\":\"Tensor::read\",\"rounds\":2,\"single_round_bytes\":"<<total<<",\"explicit_wait_or_reset\":false,\"direct_device_dereference\":false,\"sources\":[";
    for(size_t slot=0;slot<info.size();++slot){const auto& i=info[slot];if(slot){index<<',';}
        fields(index,i,slot);index<<",\"reads\":[";
        for(size_t round=0;round<2;++round){const auto& item=owned[round*sources.size()+slot];const auto name="round"+std::to_string(round)+".input"+std::to_string(slot)+".f32";
            std::ofstream f(directory/name,std::ios::binary);f.write(item.bytes.data(),std::streamsize(item.bytes.size()));f.close();need(bool(f),"Source bytes write");
            if(round){index<<',';}index<<"{\"round\":"<<round<<",\"file\":"<<quote(name)<<",\"begin_ns\":"<<item.begin<<",\"end_ns\":"<<item.end<<"}";
        }index<<"]}";
    }index<<"]}\n";index.close();need(bool(index),"Source index write");
}
}
