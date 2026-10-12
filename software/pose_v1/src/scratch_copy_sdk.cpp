#include "scratch_copy_sdk.hpp"
#include <icraft-backends/hostbackend/backend.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <thread>
#include <stdexcept>
namespace pose::scratch {
namespace {namespace xrt=icraft::xrt;namespace xir=icraft::xir;void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}}
struct SdkScratch::Impl {
    std::thread::id owner=std::this_thread::get_id();xrt::Device device;std::array<xrt::Tensor,2> source;
    void check()const{need(owner==std::this_thread::get_id(),"Scratch SDK owner changed");}
    explicit Impl(const std::filesystem::path& out){
        need(!std::filesystem::exists(out),"Preserve scratch SDK evidence");std::filesystem::create_directory(out);
        const std::string url="axi://zg330aiu?npu=0x40000000&dma=0x80000000";
        device=xrt::Device::Open(url);device.setWaitTime(10000);const auto versions=device.version();
        need(versions.count("device")&&versions.at("device")=="25122301"&&versions.count("icore")&&versions.at("icore")=="FMSHZGV3TECH-AID - 24160628","Scratch device baseline differs");
        auto region=device.defaultMemRegion();need(region.device().same_as(device)&&!region.same_as(xrt::HostDevice::MemRegion())&&std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Scratch region baseline differs");
        std::ofstream f(out/"regions.json");f<<"{\"url\":"<<std::quoted(url)<<",\"device\":"<<std::quoted(versions.at("device"))<<",\"icore\":"<<std::quoted(versions.at("icore"))<<",\"full_model_Session\":false,\"NPU_forward\":false,\"region_identity\":"<<reinterpret_cast<uintptr_t>(region.operator->())<<",\"sources\":[";
        for(size_t i=0;i<2;++i){auto type=xir::TensorType(xir::FloatType::FP32(),{int64_t(sizes[i]/4)},xir::Layout("C"));source[i]=xrt::Tensor(type).mallocOn(region);const auto&t=source[i];
            need(t.hasData()&&(t.data().ptype()==xrt::PtrType::ADDR||t.data().ptype()==xrt::PtrType::BOTH)&&t.offset()<=t.chunk()->byte_size&&sizes[i]<=t.chunk()->byte_size-t.offset(),"Scratch source storage differs");
            if(i)f<<',';
            f<<"{\"slot\":"<<i<<",\"bytes\":"<<sizes[i]<<",\"pointer\":\""<<(t.data().ptype()==xrt::PtrType::ADDR?"ADDR":"BOTH")<<"\",\"region\":"<<std::quoted(std::string(t.memRegion()->typeKey()))<<",\"region_identity\":"<<reinterpret_cast<uintptr_t>(t.memRegion().operator->())<<",\"address\":"<<t.data().addr()<<",\"offset\":"<<t.offset()<<",\"capacity\":"<<t.chunk()->byte_size<<'}';
        }f<<"]}\n";f.close();need(bool(f),"Scratch identity save failed");
        auto a=source[0].data().addr(),b=source[1].data().addr();need(a!=b&&(a<b?b-a>=sizes[0]:a-b>=sizes[1]),"Scratch device sources overlap");
        // Validate both allocations before the first device-data write.
        for(size_t i=0;i<2;++i){auto bytes=pattern(i);auto host=xrt::Tensor(source[i].dtype()).mallocOn(xrt::HostDevice::MemRegion());host.write(0,bytes.data(),bytes.size());source[i].copyFrom(0,host,0,bytes.size());}
    }
};
SdkScratch::SdkScratch(const std::filesystem::path& out):p_(std::make_unique<Impl>(out)){}
SdkScratch::~SdkScratch()=default;
Pair SdkScratch::readSources(){p_->check();Pair pair;for(size_t i=0;i<2;++i){pair.values[i].resize(sizes[i]);pair.copyBegin[i]=now();p_->source[i].read(pair.values[i].data(),0,sizes[i]);pair.copyEnd[i]=now();}return pair;}
Pair SdkScratch::copyPair(){p_->check();Pair pair;for(size_t i=0;i<2;++i){auto dest=xrt::Tensor(p_->source[i].dtype()).mallocOn(xrt::HostDevice::MemRegion());need(dest.data().ptype()==xrt::PtrType::CPTR&&dest.offset()<=dest.chunk()->byte_size&&sizes[i]<=dest.chunk()->byte_size-dest.offset(),"Scratch Host destination differs");
    pair.copyBegin[i]=now();dest.copyFrom(0,p_->source[i],0,sizes[i]);pair.copyEnd[i]=now();pair.shadowBegin[i]=now();pair.values[i]=own(dest.data().cptr(),sizes[i]);pair.shadowEnd[i]=now();}return pair;}
}
