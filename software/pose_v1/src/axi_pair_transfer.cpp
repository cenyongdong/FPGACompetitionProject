#include "axi_pair_probe.hpp"
#include "input_read_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <stdexcept>
namespace pose::axi_probe {
void transfer(const icraft::xrt::Tensor&src,icraft::xrt::Tensor&dst,Method method){
    namespace xrt=icraft::xrt;
    if(method!=Method::Copy&&method!=Method::Read)throw std::runtime_error("Unknown transfer method");
    if(!src.defined()||!dst.defined()||!src.hasData()||!dst.hasData()||src.dtype()!=dst.dtype()||
       !src.dtype()->element_dtype.isFP32()||(src.dtype().bytes()!=30240&&src.dtype().bytes()!=16800)||
       !dst.isOn(xrt::HostDevice::MemRegion())||dst.data().ptype()!=xrt::PtrType::CPTR||
       src.offset()>src.chunk()->byte_size||src.dtype().bytes()>src.chunk()->byte_size-src.offset()||
       dst.offset()>dst.chunk()->byte_size||dst.dtype().bytes()>dst.chunk()->byte_size-dst.offset()||
       src.chunk().same_as(dst.chunk()))throw std::runtime_error("Transfer storage/type/ownership differs");
    if(method==Method::Read){pose::input_read::intoHost(src,dst);}
    else{dst.copyFrom(0,src,0,size_t(src.dtype().bytes()));}
}
}
