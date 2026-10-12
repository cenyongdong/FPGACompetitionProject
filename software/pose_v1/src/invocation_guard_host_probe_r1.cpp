#include "pipeline_fixture_source.hpp"
#include "host_failure_evidence.hpp"
#include "failure_source_readback.hpp"
#include "mixed_bridge.hpp"
#include "host_stage_observation.hpp"
#include "invocation_evidence.hpp"
#include <memory>
#include <cstring>
#include <stdexcept>
void host_failure_adapter_test(const std::filesystem::path& package,const std::filesystem::path& out){
    namespace xir=icraft::xir;namespace xrt=icraft::xrt;
    // Host gate local log has ended; use an explicitly empty public bridge context.
    pose_v1::mixed_candidate::configure(nullptr,false);
    auto graph=xir::Network::CreateFromJsonFile((package/"graph/piw24_ZG.json").string());auto op=graph.getOpById(192);
    std::vector<xrt::Tensor> inputs;std::vector<std::vector<float>> values;
    for(const auto& v:op->inputs){if(v.isParams())throw std::runtime_error("GatherElements test parameter baseline differs");
        values.emplace_back(size_t(v.tensorType().bytes())/sizeof(float),0.0f);
        if(inputs.size()==1)values.back()[0]=0.5f;
        auto t=xrt::Tensor(v.tensorType()).mallocOn(xrt::HostDevice::MemRegion());
        t.write(0,reinterpret_cast<char*>(values.back().data()),v.tensorType().bytes());inputs.push_back(t);
    }
    if(inputs.size()!=2)throw std::runtime_error("Failure probe arity baseline differs");
    auto frame=std::make_shared<pose::invocation_evidence::Frame>();
    pose::stage_observation::configure(out/"copy-observations",[frame](uint64_t id,uint64_t invocation,int64_t opId,size_t slot,std::vector<char> bytes){
        frame->begin(id,invocation);frame->record(opId,slot,std::move(bytes));
    });
    pose::failure_evidence::configure(out/"failed-host-inputs");
    pose::source_diagnostic::configure(out/"failed-host-inputs/source-readback");pose_v1::mixed_candidate::set_frame(42,0);
    bool rejected=false;
    try{pose_v1::mixed_candidate::forward(op,inputs,{});}catch(const pose_v1::cpu_candidate::Rejection& e){
        rejected=std::string(e.what()).find("floating-point index is not a finite integer")!=std::string::npos;
    }
    if(!rejected)throw std::runtime_error("Failure probe did not preserve the kernel rejection");
    for(size_t i=0;i<inputs.size();++i){std::vector<char> blob(values[i].size()*4);std::ifstream f(out/"failed-host-inputs"/("input"+std::to_string(i)+".f32"),std::ios::binary);
        f.read(blob.data(),std::streamsize(blob.size()));
        if(!f||std::memcmp(blob.data(),values[i].data(),blob.size())!=0)throw std::runtime_error("Failure probe captured bytes differ");
    }
    for(size_t round=0;round<2;++round)for(size_t i=0;i<inputs.size();++i){
        std::vector<char> blob(values[i].size()*4);const auto file="round"+std::to_string(round)+".input"+std::to_string(i)+".f32";
        std::ifstream source(out/"failed-host-inputs/source-readback"/file,std::ios::binary);source.read(blob.data(),std::streamsize(blob.size()));
        if(!source||std::memcmp(blob.data(),values[i].data(),blob.size())!=0)throw std::runtime_error("Host source readback bytes differ");
    }
    if(std::filesystem::exists(out/"failed-host-inputs/capture-error.txt"))throw std::runtime_error("Failure probe capture failed");
    // Real Host forward succeeds; a later full-result gate is deliberately rejected.
    for(size_t i=0;i<inputs.size();++i){std::fill(values[i].begin(),values[i].end(),0.0f);
        inputs[i].write(0,reinterpret_cast<char*>(values[i].data()),values[i].size()*4);}
    pose_v1::mixed_candidate::set_frame(43,1);
    auto result=pose_v1::mixed_candidate::forward(op,inputs,{});
    if(result.empty()||frame->inputs()!=2||frame->bytes()!=47040)throw std::runtime_error("Finite Host probe coverage differs");
    // Release actual SDK inputs/results before persisting the independently owned copy.
    inputs.clear();result.clear();values.clear();
    auto original=std::make_exception_ptr(std::runtime_error("Synthetic final complete-output rejection"));bool tail=false;
    pose::invocation_evidence::flush({
        {"complete-results",[]{throw std::runtime_error("Repeated complete-output rejection");}},
        {"failed-Host-frame",[&]{frame->save(out/"finite-output-probe");}},
        {"copy-metadata",[]{pose::stage_observation::saveMetadata();}},
        {"remaining-evidence",[&]{tail=true;}}
    },original,out/"finite-output-ledger.json");
    bool preserved=false;try{std::rethrow_exception(original);}catch(const std::runtime_error& e){preserved=std::string(e.what())=="Synthetic final complete-output rejection";}
    if(!preserved||!tail)throw std::runtime_error("Final rejection persistence blocked or replaced");
    for(size_t i=0;i<2;++i){std::ifstream owned(out/"finite-output-probe"/("op192.slot"+std::to_string(i)+".f32"),std::ios::binary);
        std::vector<char> blob(size_t(op->inputs[i].tensorType().bytes()));owned.read(blob.data(),blob.size());
        if(!owned||std::any_of(blob.begin(),blob.end(),[](char c){return c!=0;}))throw std::runtime_error("Released Host probe owned bytes differ");}
    std::ofstream contract(out/"finite-output-probe.json");contract<<"{\"status\":\"passed\",\"Host_forward_completed\":true,\"owned_inputs\":2,\"owned_bytes\":47040,\"original_error_preserved\":true,\"source_device_read\":false}\n";
    std::ofstream f(out/"failure-probe.json");f<<"{\"status\":\"passed\",\"op_id\":192,\"original_rejection_preserved\":true,\"Host_staged_bytes_match\":true,\"device_opened\":false}\n";
}

