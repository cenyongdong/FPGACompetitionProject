#include "pipeline_fixture_source.hpp"
#include "host_failure_evidence.hpp"
#include "mixed_bridge.hpp"
#include <cstring>
#include <stdexcept>
void host_failure_adapter_test(const std::filesystem::path& package,const std::filesystem::path& out){
    namespace xir=icraft::xir;namespace xrt=icraft::xrt;
    auto graph=xir::Network::CreateFromJsonFile((package/"graph/piw24_ZG.json").string());auto op=graph.getOpById(192);
    std::vector<xrt::Tensor> inputs;std::vector<std::vector<float>> values;
    for(const auto& v:op->inputs){if(v.isParams())throw std::runtime_error("GatherElements test parameter baseline differs");
        values.emplace_back(size_t(v.tensorType().bytes())/sizeof(float),0.0f);
        if(inputs.size()==1)values.back()[0]=0.5f;
        auto t=xrt::Tensor(v.tensorType()).mallocOn(xrt::HostDevice::MemRegion());
        t.write(0,reinterpret_cast<char*>(values.back().data()),v.tensorType().bytes());inputs.push_back(t);
    }
    if(inputs.size()!=2)throw std::runtime_error("Failure probe arity baseline differs");
    pose::failure_evidence::configure(out/"failed-host-inputs");pose_v1::mixed_candidate::set_frame(42,0);
    bool rejected=false;
    try{pose_v1::mixed_candidate::forward(op,inputs,{});}catch(const pose_v1::cpu_candidate::Rejection& e){
        rejected=std::string(e.what()).find("floating-point index is not a finite integer")!=std::string::npos;
    }
    if(!rejected)throw std::runtime_error("Failure probe did not preserve the kernel rejection");
    for(size_t i=0;i<inputs.size();++i){std::vector<char> blob(values[i].size()*4);std::ifstream f(out/"failed-host-inputs"/("input"+std::to_string(i)+".f32"),std::ios::binary);
        f.read(blob.data(),std::streamsize(blob.size()));
        if(!f||std::memcmp(blob.data(),values[i].data(),blob.size())!=0)throw std::runtime_error("Failure probe captured bytes differ");
    }
    if(std::filesystem::exists(out/"failed-host-inputs/capture-error.txt"))throw std::runtime_error("Failure probe capture failed");
    std::ofstream f(out/"failure-probe.json");f<<"{\"status\":\"passed\",\"op_id\":192,\"original_rejection_preserved\":true,\"Host_staged_bytes_match\":true,\"device_opened\":false}\n";
}
