#include "producer_payload.hpp"
#include "mixed_fusion_baseline.hpp"
#include <icraft-xrt/core/tensor.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xir/core/network.h>
#include <iostream>
int main(int argc,char**argv){try{
    using namespace pose::producer;namespace xrt=icraft::xrt;namespace xir=icraft::xir;need(argc==4,"GRAPH PATTERNS FRESH-OUTPUT required");std::filesystem::path out=argv[3];need(!std::filesystem::exists(out),"Preserve Host read results");std::filesystem::create_directory(out);
    auto graph=xir::Network::CreateFromJsonFile(argv[1]);auto selected=graph.view(pose_v1::fusion_baseline::members.at(9186));auto values=selected.outputs();need(values.size()==2,"Host source count differs");
    for(unsigned pattern=0;pattern<2;++pattern){const auto p=load(std::filesystem::path(argv[2])/("pattern-"+std::to_string(pattern)));
        for(size_t i=0;i<2;++i){need(values[i]->v_id==outputIds[i]&&values[i].storageBytes()==outputSizes[i],"Host source specification differs");auto t=xrt::Tensor(values[i].tensorType()).mallocOn(xrt::HostDevice::MemRegion());need(t.data().ptype()==xrt::PtrType::CPTR,"Host source not CPTR");auto owned=p.expected[i];t.write(0,owned.data(),owned.size());
            for(unsigned round=0;round<2;++round){Bytes bytes(outputSizes[i]);t.read(bytes.data(),0,bytes.size());need(bytes==p.expected[i],"Public Host read differs");saveFile(out/(std::to_string(pattern)+"-"+std::to_string(round)+"-"+std::to_string(outputIds[i])+".f32"),bytes);}}
    }
    std::cout<<"Public Tensor::read Host CPTR8 owned outputs188160 bytes passed; no physical Device/Session\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
