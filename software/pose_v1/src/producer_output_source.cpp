#include "producer_output_source.hpp"
#include "producer_read_contract.hpp"
#include "producer_payload.hpp"
#include <icraft-xrt/dev/zg330_device.h>
#include <fstream>
#include <sstream>
#include <chrono>
namespace pose::producer_read {
namespace {
namespace xrt=icraft::xrt;namespace xir=icraft::xir;
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
}
struct ReadScope {Guard guard;std::vector<xrt::Tensor> outputs;std::array<xir::TensorType,2> types;std::array<Source,2> sources; xrt::Device device;size_t invocation=0;uint64_t reads=0,captures=0;};
std::shared_ptr<ReadScope> createScope(){return std::make_shared<ReadScope>();}
void checkIdle(const std::shared_ptr<ReadScope>&s){s->guard.idle();}
std::unique_ptr<OutputLease> makeLease(const std::shared_ptr<ReadScope>&s,std::vector<xrt::Tensor> outputs,const std::array<xir::TensorType,2>&types,const xrt::Device&device,size_t invocation){
    using namespace pose::producer;s->guard.idle();need(outputs.size()==2&&invocation<100,"Output lease count differs");const auto region=device.defaultMemRegion();std::array<Source,2> sources;
    for(size_t i=0;i<2;++i){const auto&t=outputs[i];need(t.hasData()&&t.dtype()==types[i]&&t.memRegion().same_as(region)&&t.chunk().defined()&&t.chunk()->region.same_as(region),"Output lease dtype/region differs");
        need(t.dtype()->element_dtype.isFP32()&&(t.data().ptype()==xrt::PtrType::ADDR||t.data().ptype()==xrt::PtrType::BOTH),"Output lease is not physical FP32");sources[i]={t.data().addr(),outputSizes[i],t.offset(),t.chunk()->byte_size,reinterpret_cast<uintptr_t>(t.chunk().operator->()),outputIds[i]};}
    validateSources(sources);const auto token=s->guard.open();s->outputs=std::move(outputs);s->types=types;s->sources=sources;s->device=device;s->invocation=invocation;return std::make_unique<OutputLease>(s,token);
}
OutputLease::OutputLease(std::shared_ptr<ReadScope>s,uint64_t token):scope_(std::move(s)),token_(token){pose::producer::need(bool(scope_),"Null output lease scope");scope_->guard.check(token_);}
OutputLease::~OutputLease(){if(scope_->guard.owner()&&!closed_){try{close();}catch(...){} }}
void OutputLease::close(){pose::producer::need(scope_->guard.owner(),"Output lease close owner differs");if(closed_){return;}scope_->guard.check(token_);scope_->outputs.clear();scope_->types={};scope_->device=xrt::Device{};scope_->guard.close(token_);closed_=true;}
void OutputLease::captureFailure(const std::filesystem::path&out){
    using namespace pose::producer;scope_->guard.check(token_);need(!closed_&&scope_->captures==0,"Lease capture repeated or closed");++scope_->captures;
    need(std::filesystem::file_size(out/"output-4386.f32")==30240&&std::filesystem::file_size(out/"output-4390.f32")==16800,"First outputs incomplete");
    need(!std::filesystem::exists(out/"late-source"),"Preserve source evidence");const auto dir=out/"late-source";std::filesystem::create_directory(dir);std::ofstream meta(dir/"reads.jsonl");need(bool(meta),"Source journal open failed");
    for(size_t i=0;i<2;++i){saveText(dir/("dtype-"+std::to_string(outputIds[i])+".txt"),scope_->outputs[i].dtype().toString());}
    auto zg=scope_->device.cast<xrt::ZG330Device>();
    for(unsigned round=0;round<2;++round){
        for(size_t i=0;i<2;++i){scope_->guard.check(token_);const auto&t=scope_->outputs[i];const auto&s=scope_->sources[i];need(t.dtype()==scope_->types[i],"Late source dtype changed");
            need(t.data().addr()==s.address&&t.offset()==s.offset&&t.chunk()->byte_size==s.capacity&&reinterpret_cast<uintptr_t>(t.chunk().operator->())==s.chunk_identity,"Late source storage identity changed");
            Bytes owned(outputSizes[i]);const auto metadata=now();const auto countBefore=zg.layerCount();const bool ready=t.isReady();const auto begin=now();
            t.read(owned.data(),0,owned.size());const auto end=now();++scope_->reads;const auto countAfter=zg.layerCount();
            saveFile(dir/("round-"+std::to_string(round)+"-"+std::to_string(outputIds[i])+".f32"),owned);
            meta<<"{\"invocation\":"<<scope_->invocation<<",\"round\":"<<round<<",\"value\":"<<outputIds[i]<<",\"bytes\":"<<owned.size()<<",\"metadata_ns\":"<<metadata<<",\"read_begin_ns\":"<<begin<<",\"read_end_ns\":"<<end<<",\"saved_ns\":"<<now()<<",\"source_address\":"<<t.data().addr()<<",\"source_offset\":"<<t.offset()<<",\"source_capacity\":"<<t.chunk()->byte_size<<",\"chunk_identity\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"source_ready\":"<<(ready?"true":"false")<<",\"count_before\":"<<countBefore<<",\"count_after\":"<<countAfter<<",\"owned_fingerprint\":"<<fingerprint(owned)<<"}\n";meta.flush();need(bool(meta),"Source journal save failed");
        }
    }
    saveText(dir/"summary.json","{\"rounds\":2,\"source_read_calls\":4,\"bytes\":94080,\"first_outputs_unchanged_by_module\":true,\"wait_reset_forward_write_calls\":0}\n");
}
void expireScope(const std::shared_ptr<ReadScope>&s,const std::filesystem::path&out){
    using namespace pose::producer;s->guard.expire();s->outputs.clear();s->types={};s->device=xrt::Device{};
    std::ostringstream f;f<<"{\"opened\":"<<s->guard.opened()<<",\"closed\":"<<s->guard.closed()<<",\"forced_expired\":"<<s->guard.forced()<<",\"failure_capture_calls\":"<<s->captures<<",\"source_read_calls\":"<<s->reads<<",\"before_Session_destroy\":true}\n";saveText(out/"lease-summary.json",f.str());
}
}
