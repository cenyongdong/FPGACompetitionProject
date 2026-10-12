#include "axi_pair_probe.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <cstring>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{
    namespace xrt=icraft::xrt;namespace xir=icraft::xir;namespace a=pose::axi_probe;
    if(argc!=2)throw std::runtime_error("Pinned graph required");
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);size_t bytes=0,rejects=0;
    for(size_t slot=0;slot<2;++slot){auto type=graph.getOpById(192)->inputs[slot].tensorType();
        auto source=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        auto dest=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        for(size_t index:{size_t(0),size_t(1),size_t(48),size_t(100)}){
            auto expected=pose::typed_scratch::pattern(slot,index);source.write(0,expected.data(),expected.size());
            for(auto method:{a::Method::Copy,a::Method::Read}){a::transfer(source,dest,method);
                if(dest.dtype()!=type||std::memcmp(dest.data().cptr(),expected.data(),expected.size())){throw std::runtime_error("Host result/type differs");}bytes+=expected.size();}
        }
        for(auto method:{a::Method::Copy,a::Method::Read}){bool caught=false;try{a::transfer(source,source,method);}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Alias accepted");}
        bool caught=false;try{a::transfer(source,dest,static_cast<a::Method>(9));}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Unknown method accepted");
    }
    xrt::Tensor empty;for(auto method:{a::Method::Copy,a::Method::Read}){bool caught=false;try{a::transfer(empty,empty,method);}catch(const std::exception&){caught=true;++rejects;}if(!caught)throw std::runtime_error("Empty accepted");}
    if(bytes!=376320||rejects!=8)throw std::runtime_error("Host coverage differs");
    std::cout<<"{\"status\":\"passed\",\"Host_bytes\":376320,\"refusals\":8,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
