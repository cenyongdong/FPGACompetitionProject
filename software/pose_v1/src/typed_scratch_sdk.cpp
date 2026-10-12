#include "typed_scratch_sdk.hpp"
#include <icraft-backends/hostbackend/backend.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <algorithm>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <thread>
namespace pose::typed_scratch {
namespace {
namespace xrt=icraft::xrt;namespace xir=icraft::xir;
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void typeInfo(std::ostream&f,const xir::TensorType&t){
    f<<"{\"FP32\":"<<(t->element_dtype.isFP32()?"true":"false")<<",\"bytes\":"<<t.bytes()<<",\"shape\":[";
    for(size_t i=0;i<t->shape.size();++i){if(i){f<<',';}f<<t->shape[i];}
    f<<"],\"layout\":\"";for(size_t i=0;i<t->shape.size();++i){f<<t->layout.getAxisCharName(int64_t(i));}f<<"\",\"merged_axis\":[";
    for(size_t i=0;i<t->merged_distrs[0]->merged_axis.size();++i){if(i){f<<',';}f<<t->merged_distrs[0]->merged_axis[i];}
    f<<"],\"uvalue\":"<<int(t->merged_distrs[0]->uvalue)<<",\"valid_mask\":\"";
    for(bool bit:t->merged_distrs[0]->valid_mask){f<<(bit?'1':'0');}f<<"\"}";
}
void validateType(const xir::TensorType&t,size_t slot){
    const int64_t middle=slot?100:180;
    need(t->element_dtype.isFP32()&&t->shape.size()==3&&t->shape[0]==1&&t->shape[1]==middle&&t->shape[2]==42&&t.bytes()==pose::scratch::sizes[slot],"Actual192 shape/FP32/bytes differ");
    need(t->layout.numAxis()==3&&t->layout.getAxisCharName(0)=='*'&&t->layout.getAxisCharName(1)=='*'&&t->layout.getAxisCharName(2)=='C',"Actual192 layout differs");
    need(t->merged_distrs.size()==1,"Actual192 merged declaration count differs");const auto&d=t->merged_distrs[0];
    need(d->merged_axis.size()==1&&d->merged_axis[0]==2&&d->uvalue==xir::DistrUnvalidValue::ZERO&&d->valid_mask.size()==42&&std::all_of(d->valid_mask.begin(),d->valid_mask.end(),[](bool b){return b;}),"Actual192 full-valid distribution differs");
}
}
struct SdkScratch::Impl {
    std::thread::id owner=std::this_thread::get_id();xrt::Device device;std::array<xrt::Tensor,2> source;xrt::Tensor padding;
    void check()const{need(owner==std::this_thread::get_id(),"Typed SDK owner changed");}
    Impl(const std::filesystem::path&graphPath,const std::filesystem::path&out){
        need(!std::filesystem::exists(out),"Preserve typed SDK evidence");std::filesystem::create_directory(out);
        const auto graph=xir::Network::CreateFromJsonFile(graphPath);const auto op=graph.getOpById(192);
        need(op->inputs.size()==2&&op->inputs[0]->v_id==4386&&op->inputs[1]->v_id==4390&&!op->inputs[0].isParams()&&!op->inputs[1].isParams(),"Actual192 source values differ");
        std::array<xir::TensorType,2> types{op->inputs[0].tensorType(),op->inputs[1].tensorType()};
        for(size_t i=0;i<2;++i){validateType(types[i],i);}
        const std::string url="axi://zg330aiu?npu=0x40000000&dma=0x80000000";
        device=xrt::Device::Open(url);device.setWaitTime(10000);const auto versions=device.version();
        need(versions.count("device")&&versions.at("device")=="25122301"&&versions.count("icore")&&versions.at("icore")=="FMSHZGV3TECH-AID - 24160628","Typed device baseline differs");
        auto region=device.defaultMemRegion();need(region.device().same_as(device)&&!region.same_as(xrt::HostDevice::MemRegion())&&std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Typed region baseline differs");
        std::ofstream f(out/"regions.json");f<<"{\"url\":"<<std::quoted(url)<<",\"device\":"<<std::quoted(versions.at("device"))<<",\"icore\":"<<std::quoted(versions.at("icore"))<<",\"full_model_Session\":false,\"NPU_forward\":false,\"region_identity\":"<<reinterpret_cast<uintptr_t>(region.operator->())<<",\"sources\":[";
        for(size_t i=0;i<2;++i){
            if(i==1){padding=xrt::Tensor(xir::TensorType(xir::FloatType::FP32(),{8},xir::Layout("C"))).mallocOn(region);}
            source[i]=xrt::Tensor(types[i]).mallocOn(region);const auto&t=source[i];
            need(t.hasData()&&t.dtype()==types[i]&&t.memRegion().same_as(region)&&(t.data().ptype()==xrt::PtrType::ADDR||t.data().ptype()==xrt::PtrType::BOTH)&&t.offset()<=t.chunk()->byte_size&&pose::scratch::sizes[i]<=t.chunk()->byte_size-t.offset(),"Typed source storage differs");
            if(i){f<<',';}
            f<<"{\"slot\":"<<i<<",\"bytes\":"<<pose::scratch::sizes[i]<<",\"pointer\":\""<<(t.data().ptype()==xrt::PtrType::ADDR?"ADDR":"BOTH")<<"\",\"region\":"<<std::quoted(std::string(t.memRegion()->typeKey()))<<",\"region_identity\":"<<reinterpret_cast<uintptr_t>(t.memRegion().operator->())<<",\"chunk_identity\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"address\":"<<t.data().addr()<<",\"offset\":"<<t.offset()<<",\"capacity\":"<<t.chunk()->byte_size<<",\"actual_type\":";typeInfo(f,t.dtype());f<<'}';
        }
        f<<"],\"padding_bytes\":32,\"padding_address\":"<<padding.data().addr()<<",\"source_alignment_required\":64,\"dtype_source_op\":192,\"source_values\":[4386,4390]}\n";f.close();need(bool(f),"Typed region save failed");
        const auto a=source[0].data().addr(),b=source[1].data().addr();need(a!=b&&(a<b?b-a>=pose::scratch::sizes[0]:a-b>=pose::scratch::sizes[1])&&!source[0].chunk().same_as(source[1].chunk()),"Typed source ranges/chunks overlap");
        need(a%64==0&&b%64==0,"Typed source64 alignment differs");
        need(padding.hasData()&&padding.memRegion().same_as(region)&&padding.dtype().bytes()==32&&(padding.data().ptype()==xrt::PtrType::ADDR||padding.data().ptype()==xrt::PtrType::BOTH),"Typed padding differs");
        const auto pad=padding.data().addr();for(size_t i=0;i<2;++i){const auto address=source[i].data().addr();need(pad!=address&&(pad<address?address-pad>=32:pad-address>=pose::scratch::sizes[i]),"Typed padding overlaps source");}
    }
};
SdkScratch::SdkScratch(const std::filesystem::path&graph,const std::filesystem::path&out):p_(std::make_unique<Impl>(graph,out)){}
SdkScratch::~SdkScratch()=default;
void SdkScratch::writePattern(size_t index,Writes&times){
    p_->check();times=Writes{};
    for(size_t i=0;i<2;++i){auto bytes=pattern(i,index);auto host=xrt::Tensor(p_->source[i].dtype()).mallocOn(xrt::HostDevice::MemRegion());host.write(0,bytes.data(),bytes.size());
        times.begin[i]=now();p_->source[i].copyFrom(0,host,0,bytes.size());times.end[i]=now();
    }
}
void SdkScratch::readSources(Pair&pair){
    p_->check();pair=Pair{};
    for(size_t i=0;i<2;++i){Bytes bytes(pose::scratch::sizes[i]);pair.copyBegin[i]=now();p_->source[i].read(bytes.data(),0,pose::scratch::sizes[i]);pair.copyEnd[i]=now();pair.values[i]=std::move(bytes);}
}
void SdkScratch::copyPair(Pair&pair){
    p_->check();pair=Pair{};
    for(size_t i=0;i<2;++i){auto dest=xrt::Tensor(p_->source[i].dtype()).mallocOn(xrt::HostDevice::MemRegion());need(dest.dtype()==p_->source[i].dtype()&&dest.data().ptype()==xrt::PtrType::CPTR&&dest.offset()<=dest.chunk()->byte_size&&pose::scratch::sizes[i]<=dest.chunk()->byte_size-dest.offset(),"Typed Host destination differs");
        pair.copyBegin[i]=now();dest.copyFrom(0,p_->source[i],0,pose::scratch::sizes[i]);pair.copyEnd[i]=now();pair.shadowBegin[i]=now();pair.values[i]=pose::scratch::own(dest.data().cptr(),pose::scratch::sizes[i]);pair.shadowEnd[i]=now();
    }
}
}
