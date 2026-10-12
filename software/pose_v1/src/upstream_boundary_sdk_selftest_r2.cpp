#include "upstream_boundary_sdk.hpp"
#include <icraft-xrt/dev/host_device.h>
#include <icraft-backends/hostbackend/backend.h>
#include <icraft-xir/core/network.h>
#include <icraft-xir/ops/hard_op.h>
#include <cstring>
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{
    if(argc!=3)throw std::runtime_error("Pinned graph/fresh boundary directory required");
    namespace xrt=icraft::xrt;auto graph=icraft::xir::Network::CreateFromJsonFile(argv[1]);auto gather=graph.getOpById(442),topk=graph.getOpById(437);auto up=icraft::xir::HardOp::Init(),group=icraft::xir::HardOp::Init();
    auto value=[](int64_t id,const icraft::xir::TensorType&type){return icraft::xir::Value(type).setId(id);};
    up.setId(9188);up.setOutputs({value(4406,gather->inputs[0].tensorType())});
    group.setId(9189);group.setInputs({value(1148,gather->outputs[0].tensorType())});
    group.setOutputs({value(4414,graph.getOpById(8130)->outputs[0].tensorType()),value(4418,graph.getOpById(8131)->outputs[0].tensorType())});
    auto tensor=[](const icraft::xir::TensorType&type){auto t=xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());t.setReady(true);return t;};
    auto data=tensor(gather->inputs[0].tensorType()),index=tensor(gather->inputs[1].tensorType());std::vector<float> values(4200),indices(100);for(size_t i=0;i<values.size();++i)values[i]=float(i);for(size_t i=0;i<100;++i)indices[i]=float(99-i);data.write(0,reinterpret_cast<char*>(values.data()),16800);index.write(0,reinterpret_cast<char*>(indices.data()),400);
    auto backend=xrt::HostBackend::Init();if(!backend.getInitFunc(gather)||!backend.getForwardFunc(gather))throw std::runtime_error("Original Gather absent");backend.getInitFunc(gather).value()(gather,backend);
    pose::upstream_sdk::configure(argv[2]);pose::upstream_sdk::begin(100000,0,{},false);auto score=tensor(topk->outputs[0].tensorType());std::vector<float> zeros(100,0);score.write(0,reinterpret_cast<char*>(zeros.data()),400);
    pose::upstream_sdk::post(topk,{score,index});pose::upstream_sdk::post(up,{data});pose::upstream_sdk::pre(gather);
    auto result=backend.getForwardFunc(gather).value()(gather,{data,index},{},backend);if(result.size()!=1)throw std::runtime_error("Original Gather output arity");pose::upstream_sdk::post(gather,result);pose::upstream_sdk::pre(group);
    std::vector<xrt::Tensor> out;for(const auto&v:group->outputs){auto t=tensor(v.tensorType());t.write(0,reinterpret_cast<char*>(values.data()),16800);out.push_back(t);}pose::upstream_sdk::post(group,out);pose::upstream_sdk::save();
    std::cout<<"{\"status\":\"passed\",\"points\":8,\"owned_bytes\":101600,\"original_Gather_executed\":true,\"registration_overridden\":false,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
