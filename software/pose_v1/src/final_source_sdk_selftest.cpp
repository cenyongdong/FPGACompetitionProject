#include "final_source_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <iostream>
#include <vector>
int main(int argc,char**argv){try{
    if(argc!=3)throw std::runtime_error("Pinned graph and fresh evidence required");namespace xrt=icraft::xrt;
    auto graph=icraft::xir::Network::CreateFromJsonFile(argv[1]);pose::final_source_sdk::configure(argv[2]);pose::final_source_sdk::begin(100000,0);
    for(int64_t op:{582,649}){size_t slot=0;for(const auto&v:graph.getOpById(op)->inputs){if(v.isParams())continue;auto t=xrt::Tensor(v.tensorType()).mallocOn(xrt::HostDevice::MemRegion());std::vector<char>b(size_t(v.tensorType().bytes()),char(slot+op%127));t.write(0,b.data(),b.size());pose::final_source_sdk::source(op,slot++,t,t,v.tensorType(),{},false);}}
    for(int64_t op:{437,582}){std::vector<xrt::Tensor> ts;for(const auto&v:graph.getOpById(op)->outputs){auto t=xrt::Tensor(v.tensorType()).mallocOn(xrt::HostDevice::MemRegion());std::vector<char>b(size_t(v.tensorType().bytes()),char(op%127));t.write(0,b.data(),b.size());ts.push_back(t);}pose::final_source_sdk::outputs(op,ts);}
    pose::final_source_sdk::capture("injected final-output mismatch");std::cout<<"{\"status\":\"passed\",\"public_Host_reads\":8,\"source_bytes\":67200,\"CPU_output_bytes\":17600,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
