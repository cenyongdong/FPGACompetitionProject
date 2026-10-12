#include "read_phase_sdk.hpp"
#include "read_phase.hpp"
#include "input_read_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <chrono>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace pose::read_phase_sdk {
namespace {
namespace xrt=icraft::xrt;std::unique_ptr<pose::read_phase::Evidence> evidence;std::filesystem::path root;
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
std::string identity(const xrt::Tensor&t){
    need(t.defined()&&t.hasData()&&t.dtype()->element_dtype.isFP32()&&t.dtype().bytes()==16800&&t.offset()<=t.chunk()->byte_size&&t.dtype().bytes()<=t.chunk()->byte_size-t.offset(),"Read phase tensor identity differs");
    auto k=t.data().ptype();need(k==xrt::PtrType::CPTR||k==xrt::PtrType::ADDR||k==xrt::PtrType::BOTH,"Read phase pointer kind differs");
    std::ostringstream f;f<<"{\"tensor\":"<<reinterpret_cast<uintptr_t>(t.operator->())<<",\"chunk\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"region\":"<<reinterpret_cast<uintptr_t>(t.memRegion().operator->())<<",\"device\":"<<reinterpret_cast<uintptr_t>(t.memRegion().device().operator->())<<",\"address\":"<<(k==xrt::PtrType::CPTR?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr())<<",\"kind\":\""<<(k==xrt::PtrType::CPTR?"CPTR":k==xrt::PtrType::ADDR?"ADDR":"BOTH")<<"\",\"offset\":"<<t.offset()<<",\"capacity\":"<<t.chunk()->byte_size<<",\"bytes\":16800}";return f.str();
}
std::string pair(const xrt::Tensor&s,const xrt::Tensor&d){return "{\"source\":"+identity(s)+",\"destination\":"+identity(d)+"}";}
const char* hostBytes(const xrt::Tensor&t){need(t.isOn(xrt::HostDevice::MemRegion())&&t.data().ptype()==xrt::PtrType::CPTR,"Read phase snapshot must be Host CPTR");identity(t);return t.data().cptr();}
}
void configure(const std::filesystem::path&p){need(!evidence&&!std::filesystem::exists(p)&&std::filesystem::is_directory(p.parent_path()),"Preserve read phase configuration");root=p;evidence=std::make_unique<pose::read_phase::Evidence>();}
void copy(uint64_t f,uint64_t i,const xrt::Tensor&s,xrt::Tensor&d,bool host){
    const char* target=nullptr;
    if(evidence){need(s.dtype()==d.dtype(),"Read phase source/destination type differs");target=hostBytes(d);}
    if(evidence)evidence->begin(f,i,now(),pair(s,d));
    try{
        if(host){d.copyFrom(0,s,0,s.dtype().bytes());}else{pose::input_read::intoHost(s,d);}
        // Timestamp then copy into storage reserved before the original read.
        if(evidence){const auto t=now();evidence->readDone(t,"{}",target,16800);evidence->identityAfterSnapshot(false,pair(s,d));}
    }catch(const std::exception&e){if(evidence)evidence->error(now(),e.what());throw;}
}
void beforeCPU(const xrt::Tensor&t){if(evidence){const auto* data=hostBytes(t);const auto time=now();evidence->beforeCPU(time,"{}",data,16800);evidence->identityAfterSnapshot(true,identity(t));}}
void error(const std::string&s){if(evidence)evidence->error(now(),s);}
void save(){if(evidence)evidence->save(root);}
}
