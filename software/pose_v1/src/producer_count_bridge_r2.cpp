#include "mixed_bridge.hpp"
#include "host_failure_evidence.hpp"
#include "failure_source_readback.hpp"
#include "host_stage_observation.hpp"
#include "producer_count_observation.hpp"
#include "mixed_fusion_baseline.hpp"
#include <icraft-xrt/dev/zg330_device.h>
#include <cstring>
#include <sstream>
#include "application_clock.hpp"
#include "content_diagnostic.hpp"
#include <icraft-xir/ops/ops.h>
#include <chrono>
#include <iomanip>
#include <mutex>
#include <ostream>

namespace pose_v1::mixed_candidate {
namespace xir = icraft::xir;
namespace xrt = icraft::xrt;
namespace cpu = pose_v1::cpu_candidate;
namespace {
std::ostream* trace = nullptr;
bool permit_hardware = false;
xrt::Device allowed_device;
uint64_t frame_id = 0;
uint64_t invocation_id = 0;
std::mutex trace_mutex;
using Clock = std::chrono::steady_clock;
void need(bool yes, const char* code, const char* detail) {
    if (!yes) throw cpu::Rejection(code, detail);
}
bool host(const xrt::Tensor& t) {
    return t.isOn(xrt::HostDevice::MemRegion()) && t.data().ptype() == xrt::PtrType::CPTR;
}
void bounds(const xrt::Tensor& t, const xir::TensorType& type, const char* code) {
    need(t.hasData() && t.dtype() == type, code, "Data or declared dtype differs");
    need(t.offset() <= t.chunk()->byte_size && type.bytes() <= t.chunk()->byte_size-t.offset(),
         code, "Tensor extends beyond allocated chunk");
    if (!host(t)) {
        need(permit_hardware && allowed_device.defined(), "memory", "Hardware memory is forbidden in this mode");
        need(t.memRegion().device().same_as(allowed_device), "memory", "Memory belongs to an unexpected device");
        need(t.data().ptype() == xrt::PtrType::ADDR || t.data().ptype() == xrt::PtrType::BOTH,
             "memory", "Unconfirmed device memory pointer kind");
    }
}
void event(const xir::Operation& op, const char* action, size_t index,
           const xrt::Tensor& source, const xrt::Tensor& dest, Clock::time_point begin) {
    std::lock_guard<std::mutex> guard(trace_mutex);
    if (!trace) return;
    *trace << "{\"frame_id\":" << frame_id << ",\"invocation\":" << invocation_id << ",\"op_id\":" << op->op_id
           << ",\"action\":" << std::quoted(action) << ",\"index\":" << index
           << ",\"bytes\":" << source.dtype().bytes() << ",\"elapsed_ms\":"
           << std::chrono::duration<double,std::milli>(Clock::now()-begin).count() << ",\"source\":";
    tensor_info(*trace,source); *trace << ",\"destination\":"; tensor_info(*trace,dest);
    *trace << "}\n"; trace->flush();
}
void observe192(const xir::Operation& op,size_t slot,const xrt::Tensor& src,pose::producer_count::Point point){
    if(!permit_hardware||op->op_id!=192)return;
    const auto range=fusion_baseline::sync.at(9186);
    need(range.first+range.second==234,"producer","192 fusion end differs");
    const auto kind=src.data().ptype();pose::producer_count::Source source;
    source.producer=slot?8631:8629;source.bytes=src.dtype().bytes();source.offset=src.offset();source.capacity=src.chunk()->byte_size;
    source.kind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";
    source.region=std::string(src.memRegion()->typeKey());if(kind!=xrt::PtrType::CPTR)source.address=src.data().addr();
    pose::producer_count::sample(frame_id,invocation_id,slot,point,source,[&]{return allowed_device.cast<xrt::ZG330Device>().layerCount();});
}
template<class Op> void add() {
    xrt::BackendOpRegisterHelper<Op,xrt::HostBackend>()
        .set_init([](const Op& op,xrt::HostBackend) { cpu::validate_spec(op); })
        .set_forward([](const Op& op,const std::vector<xrt::Tensor>& inputs,
                        const std::vector<xrt::Tensor>& outputs,xrt::HostBackend) {
            return forward(op,inputs,outputs);
        });
}
}
void configure(std::ostream* log,bool hardware,xrt::Device device) {
    std::lock_guard<std::mutex> guard(trace_mutex);
    need(!hardware || device.defined(),"memory","Hardware bridge requires opened device identity");
    trace=log; permit_hardware=hardware; allowed_device=device;
}
void set_frame(uint64_t frame,uint64_t invocation) {
    std::lock_guard<std::mutex> guard(trace_mutex); frame_id=frame; invocation_id=invocation;
}
void tensor_info(std::ostream& out,const xrt::Tensor& t) {
    const bool allocated=t.hasData();
    out << "{\"allocated\":" << (allocated?"true":"false") << ",\"bytes\":" << t.dtype().bytes();
    if (allocated) {
        const auto kind=t.data().ptype();
        out << ",\"pointer\":" << std::quoted(kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":kind==xrt::PtrType::BOTH?"BOTH":"unknown")
            << ",\"region\":" << std::quoted(std::string(t.memRegion()->typeKey()))
            << ",\"offset\":" << t.offset() << ",\"chunk_bytes\":" << t.chunk()->byte_size;
    }
    out << '}';
}
void register_ops(const xir::Network& graph,xrt::HostBackend backend) {
    for (int64_t id : {188,192,437,582,649}) {
        auto op=graph.getOpById(id); cpu::validate_spec(op);
        need(!backend.isOpSupported(op) && !backend.getInitFunc(op) && !backend.getForwardFunc(op),
             "registry","Existing or partial registration; never override");
    }
    auto gather=graph.getOpById(442);
    need(gather.is<xir::Gather>() && backend.isOpSupported(gather) && backend.getInitFunc(gather) && backend.getForwardFunc(gather),
         "registry","Original Gather baseline changed");
    auto gi=backend.getInitFunc(gather).value().target_type().hash_code();
    auto gf=backend.getForwardFunc(gather).value().target_type().hash_code();
    add<xir::TopK>(); add<xir::GatherElements>(); add<xir::ScatterND>();
    need(backend.getInitFunc(gather).value().target_type().hash_code()==gi &&
         backend.getForwardFunc(gather).value().target_type().hash_code()==gf,
         "registry","Gather callback type changed");
    for (int64_t id : {188,192,437,582,649}) {
        auto op=graph.getOpById(id);
        need(backend.isOpSupported(op) && backend.getInitFunc(op) && backend.getForwardFunc(op),
             "registry","Mixed registration not visible");
    }
}
std::vector<xrt::Tensor> forward(const xir::Operation& op,const std::vector<xrt::Tensor>& inputs,
                                const std::vector<xrt::Tensor>& supplied) {
    {forward_clock::Span t("bridge.spec",op->op_id);cpu::validate_spec(op);}
    size_t expected=0; for (const auto& v : op->inputs) if (!v.isParams()) ++expected;
    need(inputs.size()==expected,"arity","Runtime input count differs");
    need(supplied.empty() || supplied.size()==op->outputs.size(),"output","Partial output buffers cannot be mapped safely");
    std::vector<xrt::Tensor> staged;
    pose::stage_observation::Call observation(frame_id,invocation_id,op->op_id);
    size_t index=0;
    for (const auto& value : op->inputs) {
        if (value.isParams()) continue; // Real/synthetic parameters remain in the original op.
        const auto& src=inputs[index]; bounds(src,value.tensorType(),"storage");
        observe192(op,index,src,pose::producer_count::Point::BeforeWait);
        auto begin=Clock::now();
        {forward_clock::Span t("bridge.wait",op->op_id,index);need(src.waitForReady(std::chrono::milliseconds(10000)),"ready","SDK input wait timed out");}
        const auto waitEnd=pose::stage_observation::now();
        observe192(op,index,src,pose::producer_count::Point::AfterWait);
        if(permit_hardware&&op->op_id==582&&index==0){
            // A fresh SDK execution-counter poll, not a DMA/cache fence.
            const auto range=fusion_baseline::sync.at(9189),last=fusion_baseline::sync.at(9191);
            try{auto result=pose::stage_observation::waitFresh(uint32_t(range.first+range.second),uint32_t(last.first+last.second),[&]{return allowed_device.cast<xrt::ZG330Device>().layerCount();},std::chrono::milliseconds(10000));
                pose::stage_observation::recordCompletion(frame_id,invocation_id,op->op_id,result);
            }catch(const std::exception& e){pose::stage_observation::recordSyncFailure(frame_id,invocation_id,op->op_id,e.what());throw;}
        }
        auto allocate=Clock::now();auto dst=xrt::Tensor(value.tensorType()).mallocOn(xrt::HostDevice::MemRegion());
        forward_clock::record("bridge.allocate",op->op_id,index,allocate,Clock::now());
        // SDK owns reads and cross-region copy semantics. Never dereference ADDR/BOTH.
        observe192(op,index,src,pose::producer_count::Point::BeforeCopy);
        const auto copyBegin=pose::stage_observation::now();
        {forward_clock::Span t("bridge.copy",op->op_id,index);dst.copyFrom(0,src,0,value.tensorType().bytes());}
        const auto copyEnd=pose::stage_observation::now();
        observe192(op,index,src,pose::producer_count::Point::AfterCopy);
        pose::stage_observation::Info metadata;metadata.slot=index;metadata.bytes=size_t(value.tensorType().bytes());
        metadata.sourceOffset=src.offset();metadata.sourceCapacity=src.chunk()->byte_size;metadata.sourceRegion=std::string(src.memRegion()->typeKey());
        const auto kind=src.data().ptype();metadata.sourceKind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";if(kind!=xrt::PtrType::CPTR)metadata.sourceAddress=src.data().addr();
        metadata.hostPointer=reinterpret_cast<uintptr_t>(dst.data().cptr());metadata.hostChunk=reinterpret_cast<uintptr_t>(dst.chunk().operator->());metadata.hostOffset=dst.offset();metadata.hostCapacity=dst.chunk()->byte_size;metadata.hostRegion=std::string(dst.memRegion()->typeKey());
        metadata.waitBegin=std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count();metadata.waitEnd=waitEnd;metadata.copyBegin=copyBegin;metadata.copyEnd=copyEnd;
        observation.afterCopy(std::move(metadata),dst.data().cptr());
        if(content_diagnostic::enabled())content_diagnostic::capture(dst,"bridge_input",op->op_id,index);
        staged.push_back(dst); event(op,"input_to_host",index,src,dst,begin); ++index;
    }
    for (size_t i=0;i<supplied.size();++i) bounds(supplied[i],op->outputs[i].tensorType(),"output");
    auto compute=Clock::now();std::vector<xrt::Tensor> computed;
    try{observation.validate();computed=cpu::forward(op,staged,{});}catch(const std::exception& error){
        // Successful path unchanged. All snapshots own bytes from existing Host staging.
        const auto errorTime=pose::stage_observation::now();
        if(pose::failure_evidence::enabled())try{
            std::vector<pose::failure_evidence::Blob> blobs;
            for(size_t i=0;i<staged.size();++i){const auto& t=staged[i];
                need(host(t)&&t.dtype()->element_dtype.isFP32(),"capture","Failure input must be Host CPTR FP32");
                bounds(t,t.dtype(),"capture");const auto bytes=t.dtype().bytes();
                need(bytes>0&&bytes<=1024*1024,"capture","Failure input byte bound");
                pose::failure_evidence::Blob b;b.slot=i;b.offset=t.offset();b.chunkBytes=t.chunk()->byte_size;
                for(int64_t d:t.dtype()->shape)b.shape.push_back(d);
                for(size_t a=0;a<t.dtype()->shape.size();++a)b.layout+=t.dtype()->layout.getAxisCharName(int64_t(a));
                b.distributions=t.dtype()->merged_distrs.size();b.bytes.resize(size_t(bytes));
                std::memcpy(b.bytes.data(),t.data().cptr(),size_t(bytes));blobs.push_back(std::move(b));
            }
            std::ostringstream declarations;declarations<<'[';size_t slot=0;
            for(const auto& v:op->inputs){if(slot)declarations<<',';
                declarations<<"{\"slot\":"<<slot++<<",\"parameter\":"<<(v.isParams()?"true":"false")<<",\"bytes\":"<<v.tensorType().bytes()<<",\"shape\":[";
                for(size_t j=0;j<v.tensorType()->shape.size();++j){if(j)declarations<<',';declarations<<v.tensorType()->shape[j];}declarations<<"]}";
            }
            declarations<<']';pose::failure_evidence::save(frame_id,invocation_id,op->op_id,error.what(),blobs,declarations.str());
            observation.saveFailure(pose::stage_observation::failureRoot(),errorTime);
            size_t totalBytes=0;for(const auto& b:blobs)totalBytes+=b.bytes.size();
            pose::source_diagnostic::capture(frame_id,invocation_id,op->op_id,inputs,allowed_device,permit_hardware,totalBytes);
        }catch(const std::exception& e){pose::failure_evidence::noteCaptureError(e.what());}
        catch(...){pose::failure_evidence::noteCaptureError("Unknown failure capture error");}
        throw; // Preserve the original CPU exception, never recover/retry or edit indices.
    }
    forward_clock::record("bridge.cpu",op->op_id,0,compute,Clock::now());
    if(content_diagnostic::enabled())for(size_t i=0;i<computed.size();++i)
        content_diagnostic::capture(computed[i],"bridge_result",op->op_id,i);
    if (supplied.empty()) return computed;
    std::vector<xrt::Tensor> returned;
    for (size_t i=0;i<computed.size();++i) {
        auto begin=Clock::now(); auto target=supplied[i];
        {forward_clock::Span t("bridge.writeback",op->op_id,i);target.copyFrom(0,computed[i],0,computed[i].dtype().bytes());}
        target.setReady(true);
        returned.push_back(target); event(op,"host_to_output",i,computed[i],target,begin);
    }
    return returned;
}
}
