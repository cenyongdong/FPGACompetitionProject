#include "producer_high_sdk.hpp"
#include "producer_address_sdk.hpp"
#include "mixed_fusion_baseline.hpp"
#include <icraft-xrt/core/session.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-backends/zg330backend/zg330backend.h>
#include <chrono>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <set>
#include <thread>
namespace pose::producer {
namespace {
namespace phase=pose::producer_phase;
template<class F> decltype(auto) observed(phase::Trace* trace,phase::Phase ph,int64_t value,F&& f){
    if(trace){return trace->run(ph,value,std::forward<F>(f));}return std::forward<F>(f)();
}
namespace xir=icraft::xir;namespace xrt=icraft::xrt;
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void checkStorage(const xrt::Tensor&t,const xir::TensorType&dt,const xrt::MemRegion&r){
    need(t.hasData()&&t.dtype()==dt&&t.memRegion().same_as(r),"Tensor type/region differs");
    need(t.chunk().defined()&&t.chunk()->region.same_as(r)&&t.offset()<=t.chunk()->byte_size&&dt.bytes()<=t.chunk()->byte_size-t.offset(),"Tensor range/owner differs");
    const auto k=t.data().ptype();need(k==xrt::PtrType::ADDR||k==xrt::PtrType::BOTH||k==xrt::PtrType::CPTR,"Unsupported pointer type");
}
}
struct SdkAddressGroup::Impl {
    bool mock;std::thread::id owner=std::this_thread::get_id();std::filesystem::path evidence;
    xir::Network graph;xir::NetworkView selected;xrt::Device device;std::unique_ptr<pose::producer_address::Reservation> reservation;xrt::Session session;
    std::array<xir::Value,2> ins,outs;
    void check()const{need(owner==std::this_thread::get_id(),"SDK owner changed");}
    Impl(const std::filesystem::path&g,const std::filesystem::path&raw,const std::filesystem::path&e,bool simulated):mock(simulated),evidence(e){
        const auto started=now();graph=xir::Network::CreateFromJsonFile(g.string());graph.lazyLoadParamsFromFile(raw.string(),true);
        const auto& members=pose_v1::fusion_baseline::members.at(9186);selected=graph.view(members);
        need(selected->ops.size()==19,"Frozen selected membership differs");
        auto input=selected.inputs(),output=selected.outputs();need(input.size()==2&&output.size()==2,"Boundary count differs");
        // Session vectors follow documented NetworkView boundary order.
        for(size_t s=0;s<2;++s){need(input[s]->v_id==inputIds[s]&&output[s]->v_id==outputIds[s],"Boundary order differs");ins[s]=input[s];outs[s]=output[s];
            need(ins[s].storageBytes()==inputSizes[s]&&outs[s].storageBytes()==outputSizes[s],"Actual boundary byte count differs");}
        device=xrt::Device::Open(mock?"mock://zg330":"axi://zg330aiu?npu=0x40000000&dma=0x80000000");device.setWaitTime(10000);
        if(!mock){const auto v=device.version();need(v.count("device")&&v.at("device")=="25122301"&&v.count("icore")&&v.at("icore")=="FMSHZGV3TECH-AID - 24160628","Physical device baseline differs");}
        need(!mock,"High address candidate requires physical region");reservation=std::make_unique<pose::producer_address::Reservation>(device,evidence);
        session=xrt::Session::Create<xrt::zg330::ZG330Backend>(selected,{device});need(session.backendBindings().size()==19,"Initial bindings differ");session.enableTimeProfile(false);session.apply();
        const auto bindings=session.backendBindings();need(bindings.size()==1&&bindings.begin()->second.is<xrt::zg330::ZG330Backend>(),"Independent deployed binding differs");
        auto backend=bindings.begin()->second.cast<xrt::zg330::ZG330Backend>();auto info=backend->forward_info;need(info.defined(),"Public ForwardInfo absent");
        const auto fused=info->hardop_map.at(bindings.begin()->first);need(fused.defined(),"Independent group metadata absent");
        need(std::set<int64_t>(fused->merge_from.begin(),fused->merge_from.end())==std::set<int64_t>(members.begin(),members.end()),"Independent fused members differ");
        need(fused->sync_idx==std::pair<int,int>{0,11}&&info->idx_map.at(bindings.begin()->first)==fused->sync_idx,"Independent sync0/11 differs");
        const auto region=device.defaultMemRegion();const auto chunks=region.memManager().getAllMemChunk();
        if(!mock){need(region.device().same_as(device)&&std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Physical region differs");}
        reservation->recordAllocated(evidence);
        std::ostringstream report;report<<"{\"mock\":"<<(mock?"true":"false")<<",\"group\":"<<bindings.begin()->first<<",\"sync_start\":0,\"layers\":11,\"member_count\":19,\"forward_calls\":0,\"physical_device_opened\":"<<(mock?"false":"true")<<",\"deployment_begin_ns\":"<<started<<",\"deployment_end_ns\":"<<now()<<",\"boundary\":[";
        for(size_t i=0;i<4;++i){const auto id=i<2?inputIds[i]:outputIds[i-2];const auto v=info->value_map.at(id);need(v.defined()&&!v->is_ocm,"Unsupported boundary OCM");
            const auto expected=i<2?inputSizes[i]:outputSizes[i-2];need(v->byte_size==expected,"Boundary mapped bytes differ");
            uint64_t owned=0,capacity=0;bool matched=false;
            for(const auto& c:chunks){if(c->begin.ptype()==xrt::PtrType::CPTR){continue;}const auto addr=c->begin.addr();
                if(v->phy_addr>=addr&&v->phy_addr-addr<=c->byte_size&&expected<=c->byte_size-(v->phy_addr-addr)){need(!matched,"Ambiguous boundary owner");matched=true;owned=addr;capacity=c->byte_size;}}
            need(matched,"Boundary range not covered by owned SDK chunk");reservation->checkBoundary(v->phy_addr,expected,owned);
            if(i){report<<',';}report<<"{\"value\":"<<id<<",\"bytes\":"<<expected<<",\"physical\":"<<v->phy_addr<<",\"logical\":"<<v->logic_addr<<",\"is_ocm\":false,\"real\":"<<(v->real?"true":"false")<<",\"alias_from\":"<<(v->real?-1:v->fake_from->v_id)<<",\"owned_chunk_start\":"<<owned<<",\"owned_chunk_capacity\":"<<capacity<<'}';
        }
        report<<"]}\n";backend.log();saveText(evidence/"deployment.json",report.str());
    }
    ~Impl(){
        session=xrt::Session{};selected=xir::NetworkView{};graph=xir::Network{};
        try{reservation->release(evidence);}catch(const std::exception&e){try{saveText(evidence/"prefix-release.error.txt",e.what());}catch(...){} }
        reservation.reset(); // Drop the address owner while Device is still alive, including failed release audits.
        try{auto chunks=device.defaultMemRegion().memManager().getAllMemChunk();std::ostringstream s;s<<"{\"session_destroyed\":true,\"remaining_sdk_chunks\":"<<chunks.size()<<"}\n";saveText(evidence/"release.json",s.str());}catch(const std::exception&e){try{saveText(evidence/"release.error.txt",e.what());}catch(...){} }
        device=xrt::Device{};
    }
    std::vector<xrt::Tensor> inputs(const Payload&p,phase::Trace* trace=nullptr){
        std::vector<xrt::Tensor> list;
        for(size_t i=0;i<2;++i){auto host=observed(trace,phase::Phase::HostAllocate,inputIds[i],[&]{return xrt::Tensor(ins[i].tensorType()).mallocOn(xrt::HostDevice::MemRegion());});
            observed(trace,phase::Phase::HostStorage,inputIds[i],[&]{checkStorage(host,ins[i].tensorType(),xrt::HostDevice::MemRegion());need(host.data().ptype()==xrt::PtrType::CPTR,"Host input not CPTR");});
            auto bytes=observed(trace,phase::Phase::InputBytes,inputIds[i],[&]{return p.inputs[i];});
            observed(trace,phase::Phase::HostWrite,inputIds[i],[&]{host.write(0,bytes.data(),bytes.size());});list.push_back(host);}
        return list;
    }
};
SdkAddressGroup::SdkAddressGroup(const std::filesystem::path&g,const std::filesystem::path&r,const std::filesystem::path&e,bool m):p_(std::make_unique<Impl>(g,r,e,m)){}
SdkAddressGroup::~SdkAddressGroup()=default;
void SdkAddressGroup::memoryRoundTrip(const Payload&p,const std::filesystem::path&out){
    p_->check();validate(p);auto inputs=p_->inputs(p);
    // Matching mock PLDDR read/write are no-ops. Test actual Host CPTR here;
    // real SDK-owned PLDDR is separately required before releasing NPU.
    const auto region=p_->mock?xrt::HostDevice::MemRegion():p_->device.defaultMemRegion();
    for(size_t i=0;i<2;++i){auto t=xrt::Tensor(p_->ins[i].tensorType()).mallocOn(region);checkStorage(t,p_->ins[i].tensorType(),region);t.copyFrom(0,inputs[i],0,inputSizes[i]);
        auto dest=xrt::Tensor(p_->ins[i].tensorType()).mallocOn(xrt::HostDevice::MemRegion());dest.copyFrom(0,t,0,inputSizes[i]);need(dest.data().ptype()==xrt::PtrType::CPTR,"Mock Host result not CPTR");
        Bytes bytes(inputSizes[i]);dest.read(bytes.data(),0,bytes.size());saveFile(out/("input-"+std::to_string(inputIds[i])+".roundtrip"),bytes);need(bytes==p.inputs[i],"SDK memory roundtrip differs");}
    saveText(out/"memory.json","{\"region\":\""+std::string(p_->mock?"HostCPTR":"physicalSDKownedPLDDR")+"\",\"forward_called\":false,\"input_bytes\":17680,\"bitwise_equal\":true}\n");
}
void SdkAddressGroup::forwardSave(const Payload&p,const std::filesystem::path&out,size_t invocation,phase::Trace& trace,uint64_t planned){
    trace.run(phase::Phase::OwnerCheck,-1,[&]{p_->check();need(!p_->mock,"Never forward on mock");});
    trace.run(phase::Phase::Validate,-1,[&]{validate(p);});auto inputs=p_->inputs(p,&trace);
    std::ofstream journal;trace.run(phase::Phase::JournalOpen,-1,[&]{journal.open(out/"stages.jsonl");need(bool(journal),"Cannot save per-call stages");});
    auto stage=[&](const char*name,int64_t value){trace.run(phase::Phase::JournalFlush,value,[&]{journal<<"{\"stage\":"<<std::quoted(name)<<",\"value\":"<<value<<",\"time_ns\":"<<now()<<"}\n";journal.flush();need(bool(journal),"Stage save failed");});};
    stage("before_reset",-1);
    auto zg=p_->device.cast<xrt::ZG330Device>();
    trace.run(phase::Phase::Deadline,-1,[&]{need(phase::beforeDeadline(planned,now()),"Prepared call missed absolute slot; no forward");});trace.check();
    const auto resetBegin=now();const auto before=trace.run(phase::Phase::Reset,-1,[&]{p_->device.reset(1);const auto v=zg.layerCount();need(v==0,"Independent counter not zero at frame boundary");return v;});
    stage("before_forward",-1);
    const auto begin=now();auto outputs=trace.run(phase::Phase::Forward,-1,[&]{return p_->session.forward(inputs);});const auto end=now();need(outputs.size()==2,"Independent output count differs");
    std::ostringstream report;report<<"{\"invocation\":"<<invocation<<",\"reset_begin_ns\":"<<resetBegin<<",\"before_forward_count\":"<<before<<",\"forward_begin_ns\":"<<begin<<",\"forward_return_ns\":"<<end<<",\"reads\":[";
    for(size_t i=0;i<2;++i){const auto&t=outputs[i];trace.run(phase::Phase::OutputStorage,outputIds[i],[&]{checkStorage(t,p_->outs[i].tensorType(),p_->device.defaultMemRegion());});
        need(t.dtype()->element_dtype.isFP32(),"Actual output not FP32");
        stage("before_wait",outputIds[i]);
        const auto waitBegin=now();trace.run(phase::Phase::Wait,outputIds[i],[&]{need(t.waitForReady(std::chrono::milliseconds(10000)),"Independent output readiness timeout");});const auto waitEnd=now();stage("after_wait",outputIds[i]);
        auto host=trace.run(phase::Phase::OutputAllocate,outputIds[i],[&]{return xrt::Tensor(t.dtype()).mallocOn(xrt::HostDevice::MemRegion());});checkStorage(host,t.dtype(),xrt::HostDevice::MemRegion());need(host.data().ptype()==xrt::PtrType::CPTR,"Host output not CPTR");
        stage("before_copy",outputIds[i]);const auto copyBegin=now();trace.run(phase::Phase::Copy,outputIds[i],[&]{host.copyFrom(0,t,0,outputSizes[i]);});const auto copyEnd=now();stage("after_copy",outputIds[i]);Bytes bytes(outputSizes[i]);trace.run(phase::Phase::HostRead,outputIds[i],[&]{host.read(bytes.data(),0,bytes.size());});const auto shadowEnd=now();
        // Owned bytes saved immediately; never reread or repair the device output.
        trace.run(phase::Phase::SaveOutput,outputIds[i],[&]{saveFile(out/("output-"+std::to_string(outputIds[i])+".f32"),bytes);});
        stage("output_saved",outputIds[i]);
        if(i){report<<',';}report<<"{\"value\":"<<outputIds[i]<<",\"wait_begin_ns\":"<<waitBegin<<",\"wait_end_ns\":"<<waitEnd<<",\"copy_begin_ns\":"<<copyBegin<<",\"copy_end_ns\":"<<copyEnd<<",\"owned_end_ns\":"<<shadowEnd<<",\"source_address\":"<<t.data().addr()<<",\"source_offset\":"<<t.offset()<<",\"source_capacity\":"<<t.chunk()->byte_size<<",\"source_chunk_identity\":"<<reinterpret_cast<uintptr_t>(t.chunk().operator->())<<",\"source_ready\":"<<(t.isReady()?"true":"false")<<",\"owned_fingerprint\":"<<fingerprint(bytes)<<'}';
    }
    const auto after=zg.layerCount();report<<"],\"after_ready_count\":"<<after<<"}\n";trace.run(phase::Phase::SaveTrace,-1,[&]{saveText(out/"trace.json",report.str());});need(after==11,"Independent completion count differs");
}
}
