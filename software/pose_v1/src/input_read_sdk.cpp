#include "input_read_sdk.hpp"
#include "input_read_contract.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <stdexcept>
namespace pose::input_read {
void intoHost(const icraft::xrt::Tensor& src,icraft::xrt::Tensor& dst){
    namespace xrt=icraft::xrt;
    if(!src.defined()||!dst.defined()||!src.hasData()||!dst.hasData()||src.dtype()!=dst.dtype()||
       !dst.isOn(xrt::HostDevice::MemRegion())||dst.data().ptype()!=xrt::PtrType::CPTR||
       src.offset()>src.chunk()->byte_size||src.dtype().bytes()>src.chunk()->byte_size-src.offset()||
       dst.offset()>dst.chunk()->byte_size||dst.dtype().bytes()>dst.chunk()->byte_size-dst.offset())
        throw std::runtime_error("Input read SDK type/storage/Host identity differs");
    if(src.chunk().same_as(dst.chunk()))throw std::runtime_error("Input read source and destination alias");
    boundedRead({dst.data().cptr(),size_t(dst.offset()),size_t(dst.chunk()->byte_size)},size_t(src.dtype().bytes()),
        [&](char* target,size_t bytes){src.read(target,0,bytes);});
}
}
