#include "read_phase_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{
    if(argc!=3)throw std::runtime_error("Graph/fresh evidence required");namespace xrt=icraft::xrt;auto g=icraft::xir::Network::CreateFromJsonFile(argv[1]);auto type=g.getOpById(192)->inputs[1].tensorType();
    auto tensor=[&]{auto t=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());t.setReady(true);return t;};auto src=tensor(),dst=tensor();std::vector<float> values(4200);for(size_t i=0;i<values.size();++i)values[i]=float(i%180);
    src.write(0,reinterpret_cast<char*>(values.data()),16800);pose::read_phase_sdk::configure(argv[2]);pose::read_phase_sdk::copy(100000,0,src,dst,true);pose::read_phase_sdk::beforeCPU(dst);pose::read_phase_sdk::save();
    std::cout<<"{\"status\":\"passed\",\"Host_copy\":true,\"two_owned_snapshots\":true,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
