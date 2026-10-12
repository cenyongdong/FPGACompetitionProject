#include "final_source_sdk.hpp"
#include "final_source_recorder.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <cstring>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace pose::final_source_sdk {
namespace {
namespace xrt=icraft::xrt;
std::unique_ptr<pose::final_source::Recorder> recorder;std::filesystem::path root;
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
void bounds(const xrt::Tensor&t){need(t.hasData()&&t.dtype()->element_dtype.isFP32(),"Recorder requires FP32 allocation");need(t.offset()<=t.chunk()->byte_size&&t.dtype().bytes()<=t.chunk()->byte_size-t.offset(),"Recorder tensor bounds differ");}
std::vector<char> owned(const xrt::Tensor&t){bounds(t);need(t.isOn(xrt::HostDevice::MemRegion())&&t.data().ptype()==xrt::PtrType::CPTR,"Recorder CPU value requires Host CPTR");need(t.dtype().bytes()>0&&t.dtype().bytes()<=16800,"Recorder Host byte bound");std::vector<char>b(size_t(t.dtype().bytes()));std::memcpy(b.data(),t.data().cptr(),b.size());return b;}
}
void configure(const std::filesystem::path&p){need(!recorder&&!std::filesystem::exists(p)&&std::filesystem::is_directory(p.parent_path()),"Preserve final recorder configuration");root=p;recorder=std::make_unique<pose::final_source::Recorder>();}
void begin(uint64_t f,uint64_t i){if(recorder)recorder->begin(f,i);}
void source(int64_t op,size_t slot,const xrt::Tensor&t,const xrt::Tensor&h,const icraft::xir::TensorType&declared,const xrt::Device&device,bool permit){
    if(!recorder||(op!=582&&op!=649))return;
    bounds(t);need(t.dtype()==declared&&h.dtype()==declared,"Recorder declared dtype differs");const auto k=t.data().ptype();const bool host=t.isOn(xrt::HostDevice::MemRegion())&&k==xrt::PtrType::CPTR;
    need(host||(permit&&device.defined()&&t.memRegion().device().same_as(device)&&(k==xrt::PtrType::ADDR||k==xrt::PtrType::BOTH)),"Recorder device ownership differs");
    std::ostringstream f;f<<"{\"tensor\":"<<reinterpret_cast<uintptr_t>(t.operator->())<<",\"chunk\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"device\":"<<reinterpret_cast<uintptr_t>(t.memRegion().device().operator->())<<",\"region\":"<<std::quoted(std::string(t.memRegion()->typeKey()))<<",\"kind\":"<<std::quoted(host?"CPTR":k==xrt::PtrType::ADDR?"ADDR":"BOTH")<<",\"address\":"<<(host?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr())<<",\"offset\":"<<t.offset()<<",\"capacity\":"<<t.chunk()->byte_size<<",\"bytes\":"<<t.dtype().bytes()<<",\"shape\":[";
    for(size_t i=0;i<declared->shape.size();++i){if(i)f<<',';f<<declared->shape[i];}f<<"],\"layout\":\"";for(size_t i=0;i<declared->shape.size();++i)f<<declared->layout.getAxisCharName(int64_t(i));f<<"\",\"distributions\":"<<declared->merged_distrs.size()<<",\"declared_matches\":true,\"owner_matches\":true}";
    // Strong public handle keeps the object alive; it does not freeze physical bytes.
    recorder->source(op,slot,f.str(),owned(h),[t,declared,region=t.memRegion(),chunk=t.chunk(),offset=t.offset(),kind=k,address=(host?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr())](char*dst,size_t n){bounds(t);need(t.dtype()==declared&&t.memRegion().same_as(region)&&t.chunk().operator->()==chunk.operator->()&&t.offset()==offset&&t.data().ptype()==kind,"Recorder late storage identity changed");need((kind==xrt::PtrType::CPTR?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr())==address,"Recorder late source address changed");need(n==t.dtype().bytes(),"Recorder late read byte bound differs");t.read(dst,0,n);});
}
void outputs(int64_t op,const std::vector<xrt::Tensor>&ts){if(!recorder||(op!=437&&op!=582))return;for(size_t i=0;i<ts.size();++i)recorder->output(op,i,owned(ts[i]));}
void capture(const std::string&e){need(bool(recorder),"Final recorder not configured");recorder->capture(root,e);}
}
