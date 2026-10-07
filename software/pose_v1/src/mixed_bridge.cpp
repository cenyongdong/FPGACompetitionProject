#include "mixed_bridge.hpp"
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
    cpu::validate_spec(op);
    size_t expected=0; for (const auto& v : op->inputs) if (!v.isParams()) ++expected;
    need(inputs.size()==expected,"arity","Runtime input count differs");
    need(supplied.empty() || supplied.size()==op->outputs.size(),"output","Partial output buffers cannot be mapped safely");
    std::vector<xrt::Tensor> staged;
    size_t index=0;
    for (const auto& value : op->inputs) {
        if (value.isParams()) continue; // Real/synthetic parameters remain in the original op.
        const auto& src=inputs[index]; bounds(src,value.tensorType(),"storage");
        auto begin=Clock::now();
        need(src.waitForReady(std::chrono::milliseconds(10000)),"ready","SDK input wait timed out");
        auto dst=xrt::Tensor(value.tensorType()).mallocOn(xrt::HostDevice::MemRegion());
        // SDK owns reads and cross-region copy semantics. Never dereference ADDR/BOTH.
        dst.copyFrom(0,src,0,value.tensorType().bytes());
        if(content_diagnostic::enabled())content_diagnostic::capture(dst,"bridge_input",op->op_id,index);
        staged.push_back(dst); event(op,"input_to_host",index,src,dst,begin); ++index;
    }
    for (size_t i=0;i<supplied.size();++i) bounds(supplied[i],op->outputs[i].tensorType(),"output");
    auto computed=cpu::forward(op,staged,{});
    if(content_diagnostic::enabled())for(size_t i=0;i<computed.size();++i)
        content_diagnostic::capture(computed[i],"bridge_result",op->op_id,i);
    if (supplied.empty()) return computed;
    std::vector<xrt::Tensor> returned;
    for (size_t i=0;i<computed.size();++i) {
        auto begin=Clock::now(); auto target=supplied[i];
        target.copyFrom(0,computed[i],0,computed[i].dtype().bytes());
        target.setReady(true);
        returned.push_back(target); event(op,"host_to_output",i,computed[i],target,begin);
    }
    return returned;
}
}
