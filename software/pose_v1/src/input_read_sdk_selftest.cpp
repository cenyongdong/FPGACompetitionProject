#include "input_read_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <vector>
int main(int argc,char**argv){try{
    namespace xrt=icraft::xrt;namespace xir=icraft::xir;
    if(argc!=2)throw std::runtime_error("Host-read test requires pinned graph");
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);size_t total=0,refused=0;
    for(size_t slot=0;slot<2;++slot){auto type=graph.getOpById(192)->inputs[slot].tensorType();
        auto src=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        auto dst=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        std::vector<char> pattern(size_t(type.bytes()));for(size_t i=0;i<pattern.size();++i)pattern[i]=char((i*17+slot*53)%251);
        src.write(0,pattern.data(),pattern.size());pose::input_read::intoHost(src,dst);
        if(std::memcmp(dst.data().cptr(),pattern.data(),pattern.size()))throw std::runtime_error("Host read differs");
        if(dst.dtype()!=type)throw std::runtime_error("Distribution declaration changed");
        total+=pattern.size();
        bool caught=false;try{pose::input_read::intoHost(src,src);}catch(const std::exception&){caught=true;++refused;}
        if(!caught)throw std::runtime_error("Alias accepted");
    }
    xrt::Tensor empty;bool caught=false;try{pose::input_read::intoHost(empty,empty);}catch(const std::exception&){caught=true;++refused;}
    if(!caught||refused!=3||total!=47040)throw std::runtime_error("Host read coverage differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":3,\"Host_read_bytes\":47040,\"types_from_op\":192,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
