#pragma once
// Validation helpers copied from the frozen r6 checker; no algorithm changes.
// Separate integration candidate. Original inference_check and CPU checker remain unchanged.
#include "mixed_bridge.hpp"
#include "mixed_fusion_baseline.hpp"
#include "content_diagnostic.hpp"
#include "preprocess.hpp"
#include <icraft-backends/zg330backend/zg330backend.h>
#include <icraft-xir/ops/ops.h>
#include <icraft-xrt/core/session.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <set>
#include <sstream>
#include <tuple>


namespace pose_v1::runtime_detail {
namespace fs=std::filesystem;
namespace xir=icraft::xir;
namespace bridge=pose_v1::mixed_candidate;
namespace content=pose_v1::content_diagnostic;
using namespace icraft::xrt;
using Clock=std::chrono::steady_clock;
inline const std::set<int64_t> host_ids={188,192,437,442,582,649};
inline constexpr const char* url="axi://zg330aiu?npu=0x40000000&dma=0x80000000";
inline void need(bool yes,const char* why) { if(!yes) throw std::runtime_error(why); }
inline void need(bool yes,const std::string& why) { if(!yes) throw std::runtime_error(why); }
inline std::string quote(const std::string& s) {
    std::ostringstream out; out << '"';
    for(unsigned char c:s) {
        if(c=='"' || c=='\\') out << '\\' << c;
        else if(c<32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str()+'"';
}
inline std::ofstream file(const fs::path& path,bool binary=false) {
    std::ofstream f(path,std::ios::out|(binary?std::ios::binary:std::ios::openmode(0)));
    need(bool(f),"Cannot save "+path.string()); f.exceptions(std::ios::failbit|std::ios::badbit);
    f << std::setprecision(17); return f;
}
inline double ms(Clock::time_point t) { return std::chrono::duration<double,std::milli>(Clock::now()-t).count(); }
inline std::vector<char> bytes(const fs::path& path,size_t expected) {
    need(fs::file_size(path)==expected,"Invalid file length: "+path.string());
    std::ifstream f(path,std::ios::binary); std::vector<char> v(expected);
    need(bool(f.read(v.data(),v.size())),"Cannot read "+path.string()); return v;
}
inline void write(const fs::path& path,const std::string& data) {
    auto f=file(path,true); f.write(data.data(),data.size());
}
inline bool shape(const xir::TensorType& t,std::initializer_list<int64_t> d) {
    return t->shape.size()==d.size() && std::equal(t->shape.begin(),t->shape.end(),d.begin());
}
inline void fp32(const xir::TensorType& t) {
    need(t->element_dtype.is<xir::FloatType>() && t->element_dtype.isFP32(),"FP32 contract differs");
}
inline void registry(const xir::Network& graph,HostBackend backend,std::ostream& out,const char* phase) {
    for(auto id:host_ids) {
        auto op=graph.getOpById(id);
        out << "{\"phase\":" << quote(phase) << ",\"op_id\":" << id
            << ",\"supported\":" << (backend.isOpSupported(op)?"true":"false")
            << ",\"init\":" << (backend.getInitFunc(op)?"true":"false")
            << ",\"forward\":" << (backend.getForwardFunc(op)?"true":"false") << "}\n";
    }
    out.flush();
}
inline void validate_graph(const xir::Network& g) {
    need(g->icraft_version=="v3.39.0" && g->icraft_xir_version=="3.39.0.0" && !g->swap_mode,"Graph version/swap differs");
    auto in=g.inputs(),out=g.outputs();
    need(in.size()==1 && out.size()==2,"Unexpected graph I/O count");
    fp32(in[0].tensorType()); fp32(out[0].tensorType()); fp32(out[1].tensorType());
    need(shape(in[0].tensorType(),{1,180,60}) && shape(out[0].tensorType(),{1,100}) && shape(out[1].tensorType(),{1,100,14,3}),"Graph output order/shape differs");
    size_t hard=0,host=0;
    for(const auto& op:g->ops) {
        if(op.is<xir::HardOp>())++hard;
        else if(host_ids.count(op->op_id)) {
            need(op->compile_target.is<xir::HostTarget>(),"Host target changed"); ++host;
        } else need(op.is<xir::Input>() || op.is<xir::Output>(),"Unexpected compute operator");
    }
    need(hard==1173 && host==6,"Frozen graph operator counts differ");
    for(auto id:{188,192,437,582,649})pose_v1::cpu_candidate::validate_spec(g.getOpById(id));
    auto gather=g.getOpById(442);
    need(gather.is<xir::Gather>() && gather.cast<xir::Gather>()->axis==0,"Gather specification differs");
}
inline void parameters(const xir::Network& g,const fs::path& output) {
    auto log=file(output/"host-parameters.jsonl"); size_t count=0;
    for(auto id:host_ids) {
        auto op=g.getOpById(id);
        for(size_t i=0;i<op->inputs.size();++i) {
            auto v=op->inputs[i]; if(!v.isParams())continue;
            auto p=v.cast<xir::Params>(); need(p.hasData(),"Real CPU parameter not materialized; stop rather than substitute");
            Tensor t(p); need(t.hasData() && t.isOn(HostDevice::MemRegion()) && t.data().ptype()==PtrType::CPTR,"Real CPU parameter memory unconfirmed");
            std::vector<float> data(t.dtype().bytes()/4);
            need(t.dtype().bytes()%4==0 && t.offset()<=t.chunk()->byte_size && t.dtype().bytes()<=t.chunk()->byte_size-t.offset(),"Parameter storage differs");
            t.read(reinterpret_cast<char*>(data.data()),0,t.dtype().bytes());
            for(float v:data)need(std::isfinite(v),"Non-finite real CPU parameter");
            if(op.is<xir::TopK>())need(data.size()==1 && data[0]==100.f,"Real K differs");
            if(op.is<xir::ScatterND>()) {
                const float limits[3]={100.f,14.f,3.f};
                for(size_t j=0;j<data.size();++j)need(data[j]==std::trunc(data[j]) && data[j]>=-limits[j%3] && data[j]<limits[j%3],"Real ScatterND index differs");
            }
            write(output/("op"+std::to_string(id)+".param"+std::to_string(i)+".f32"),
                  std::string(reinterpret_cast<char*>(data.data()),data.size()*4));
            log << "{\"op_id\":" << id << ",\"input\":" << i << ",\"value_id\":" << v->v_id
                << ",\"bytes\":" << t.dtype().bytes() << ",\"loaded_from_real_RAW\":true}\n"; ++count;
        }
    }
    need(count==4,"Real CPU parameter count differs");
}
inline Device open_device(const fs::path& output) {
    auto d=Device::Open(url); d.setWaitTime(10000); const auto v=d.version();
    auto report=file(output/"device-version.json"); report << "{\"url\":" << quote(url) << ",\"versions\":{";
    bool first=true; for(const auto& p:std::map<std::string,std::string>(v.begin(),v.end())) {
        if(!first)report << ','; first=false; report << quote(p.first) << ':' << quote(p.second);
    }
    report << "},\"numerical_accepted\":false}\n"; report.close();
    need(v.count("device") && v.at("device")=="25122301" && v.count("icore") && v.at("icore")=="FMSHZGV3TECH-AID - 24160628","Runtime FPGA/icore differs; stop");
    return d;
}
inline std::string dump(const Tensor& t,size_t count) {
    std::ostringstream s(std::ios::out|std::ios::binary);t.dump(s,"SFB");auto raw=s.str();
    need(raw.size()==count*4,"Logical output length differs");
    for(size_t i=0;i<count;++i){float f;std::memcpy(&f,raw.data()+i*4,4);need(std::isfinite(f),"Non-finite model output");}
    return raw;
}
// Candidate diagnostic: read public metadata only. Never invoke autoMerge again.
inline void snapshot_bindings(const Session& session,const xir::Network& original,
                              const fs::path& output,const std::string& phase) {
    auto all=file(output/(phase+".all-bindings.jsonl"));
    const auto bindings=session.backendBindings();
    for(const auto& item:std::map<int64_t,Backend>(bindings.begin(),bindings.end()))
        all << "{\"binding_key\":" << item.first << ",\"backend\":"
            << quote(std::string(item.second->typeKey())) << "}\n";
    auto views=file(output/(phase+".views.jsonl"));
    auto emit_view=[&](const xir::NetworkView& view,const std::string& owner) {
        if(!view.defined()){views << "{\"owner\":" << quote(owner) << ",\"defined\":false}\n";return;}
        size_t index=0;
        for(const auto& op:view->ops)
            views << "{\"owner\":" << quote(owner) << ",\"index\":" << index++
                  << ",\"op_id\":" << op->op_id << ",\"operator\":" << quote(std::string(op->typeKey()))
                  << ",\"is_hardop\":" << (op.is<xir::HardOp>()?"true":"false") << "}\n";
    };
    emit_view(original.view(),"original_graph");
    emit_view(session->network_view,"session_view");
    auto hard=file(output/(phase+".zg-hardop-map.jsonl"));
    auto sync=file(output/(phase+".zg-sync-map.jsonl"));
    auto inventories=file(output/(phase+".backends.jsonl"));
    for(size_t i=0;i<session->backends.size();++i) {
        const auto& backend=session->backends[i];
        const auto owner="backend_"+std::to_string(i);
        inventories << "{\"backend_index\":" << i << ",\"backend\":"
                    << quote(std::string(backend->typeKey())) << "}\n";
        emit_view(backend->network_view,owner);
        if(!backend.is<zg330::ZG330Backend>())continue;
        auto zg=backend.cast<zg330::ZG330Backend>();
        const auto info=zg->forward_info;
        if(!info.defined())continue;
        for(const auto& item:info->hardop_map) {
            hard << "{\"backend_index\":" << i << ",\"op_id\":" << item.first
                 << ",\"entry_defined\":" << (item.second.defined()?"true":"false");
            if(item.second.defined()) {
                hard << ",\"sync_index\":" << item.second->sync_idx.first
                     << ",\"layer_count\":" << item.second->sync_idx.second;
                if(item.second->net_hardop.defined())hard << ",\"net_hardop_id\":" << item.second->net_hardop->op_id;
                hard << ",\"merge_from\":[";
                for(size_t j=0;j<item.second->merge_from.size();++j) {
                    if(j)hard << ',';
                    hard << item.second->merge_from[j];
                }
                hard << ']';
            }
            hard << "}\n";
        }
        for(const auto& item:info->idx_map)
            sync << "{\"backend_index\":" << i << ",\"map_key\":" << item.first
                 << ",\"sync_index\":" << item.second.first << ",\"layer_count\":" << item.second.second << "}\n";
    }
}

// Validate logical membership independently of deployed (merged) binding keys.
inline std::map<int64_t,xir::Operation> checked_originals(const Session& session,const xir::Network& graph) {
    std::map<int64_t,xir::Operation> ops;
    std::set<int64_t> hard,host;
    for(const auto& op:graph->ops) {
        need(ops.emplace(op->op_id,op).second,"Duplicate original operation ID");
        (op.is<xir::HardOp>()?hard:host).insert(op->op_id);
    }
    need(ops.size()==1181 && hard.size()==1173 && host==pose_v1::fusion_baseline::host_ids,
         "Original logical graph baseline differs");
    need(session->backends.size()==2 && session->backends[0].is<zg330::ZG330Backend>() &&
         session->backends[1].is<HostBackend>(),"Backend inventory differs from reviewed baseline");
    auto view_ids=[&](const xir::NetworkView& view) {
        need(view.defined(),"Undefined runtime network view");
        std::set<int64_t> ids;
        for(const auto& op:view->ops) {
            auto original=ops.find(op->op_id);
            need(original!=ops.end() && ids.insert(op->op_id).second,"Unknown or duplicate runtime view member");
            need(std::string(op->typeKey())==std::string(original->second->typeKey()),"Runtime view operator type changed");
        }
        return ids;
    };
    std::set<int64_t> all=hard;all.insert(host.begin(),host.end());
    need(view_ids(session->network_view)==all && view_ids(session->backends[0]->network_view)==hard &&
         view_ids(session->backends[1]->network_view)==host,"Runtime view coverage differs");
    return ops;
}

inline void validate_created_bindings(const Session& session,const xir::Network& graph) {
    const auto ops=checked_originals(session,graph);
    const auto bindings=session.backendBindings();
    need(bindings.size()==ops.size(),"Create binding coverage differs");
    for(const auto& item:ops) {
        auto found=bindings.find(item.first);
        need(found!=bindings.end(),"Original operation missing create binding");
        const auto& expected=session->backends[item.second.is<xir::HardOp>()?0:1];
        need(found->second.same_as(expected),"Original operation assigned to wrong create backend");
    }
}

inline void validate_applied_bindings(const Session& session,const xir::Network& graph,const fs::path& output) {
    const auto ops=checked_originals(session,graph);
    const auto bindings=session.backendBindings();
    const auto& zg_backend=session->backends[0];
    const auto& host_backend=session->backends[1];
    const auto info=zg_backend.cast<zg330::ZG330Backend>()->forward_info;
    need(info.defined(),"Undefined ZG forward metadata");
    need(bindings.size()==15,"Deployed binding count differs from reviewed baseline");
    std::set<int64_t> hard,expected_map_keys,observed_map_keys,observed_sync_keys,groups;
    for(const auto& item:ops)if(item.second.is<xir::HardOp>())hard.insert(item.first);
    expected_map_keys=hard;
    for(const auto& item:pose_v1::fusion_baseline::members)expected_map_keys.insert(item.first);
    for(const auto& item:info->hardop_map)observed_map_keys.insert(item.first);
    for(const auto& item:info->idx_map)observed_sync_keys.insert(item.first);
    need(observed_map_keys==expected_map_keys && observed_sync_keys==expected_map_keys,"ZG metadata key coverage differs");
    for(const auto& item:info->hardop_map) {
        const auto& entry=item.second;
        need(entry.defined() && entry->net_hardop.defined() && entry->net_hardop->op_id==item.first,
             "ZG map operation identity differs");
        const auto sync=info->idx_map.find(item.first);
        need(sync!=info->idx_map.end() && sync->second==entry->sync_idx &&
             entry->sync_idx.first>=0 && entry->sync_idx.second>=0,"ZG sync metadata differs");
        if(hard.count(item.first))need(entry->merge_from.empty(),"Original ZG entry unexpectedly merged");
    }
    std::map<int64_t,int64_t> effective;
    for(const auto& item:bindings) {
        if(item.second.same_as(host_backend)) {
            need(pose_v1::fusion_baseline::host_ids.count(item.first)>0,"Unexpected deployed Host binding");
            continue;
        }
        need(item.second.same_as(zg_backend) && item.second.is<zg330::ZG330Backend>(),"Unknown deployed backend instance");
        auto baseline=pose_v1::fusion_baseline::members.find(item.first);
        need(baseline!=pose_v1::fusion_baseline::members.end() && groups.insert(item.first).second,
             "Unexpected deployed ZG execution group");
        const auto entry=info->hardop_map.find(item.first)->second;
        need(entry->sync_idx.second>0 && entry->sync_idx==pose_v1::fusion_baseline::sync.at(item.first),
             "Bound ZG group sync baseline changed");
        std::set<int64_t> members(entry->merge_from.begin(),entry->merge_from.end());
        need(members.size()==entry->merge_from.size() &&
             members==std::set<int64_t>(baseline->second.begin(),baseline->second.end()),
             "ZG group membership changed or duplicated");
        for(auto id:entry->merge_from)
            need(hard.count(id)>0 && effective.emplace(id,item.first).second,"Extra or multiply covered original HardOp");
    }
    need(groups.size()==7 && effective.size()==1173,"Incomplete original HardOp fusion coverage");
    for(auto id:pose_v1::fusion_baseline::host_ids) {
        auto binding=bindings.find(id);
        need(binding!=bindings.end() && binding->second.same_as(host_backend) && binding->second.is<HostBackend>(),
             "Required original Host binding changed");
    }
    auto bind=file(output/"bindings.jsonl");
    for(const auto& op:graph->ops) {
        const bool is_hard=op.is<xir::HardOp>();
        const auto target=is_hard?effective.at(op->op_id):op->op_id;
        const auto backend=bindings.at(target);
        bind << "{\"op_id\":" << op->op_id << ",\"operator\":" << quote(std::string(op->typeKey()))
             << ",\"is_hardop\":" << (is_hard?"true":"false")
             << ",\"effective_op_id\":" << target
             << ",\"binding_kind\":" << quote(is_hard?"zg_merge_from":"host_direct")
             << ",\"backend\":" << quote(std::string(backend->typeKey())) << "}\n";
    }
    auto summary=file(output/"binding-summary.json");
    summary << "{\"original_ops\":1181,\"original_hardops\":1173,\"direct_host_ops\":8,"
               "\"effective_zg_groups\":7,\"coverage_complete\":true}\n";
}

inline void host_content_check(const xir::Network& graph,const fs::path& output) {
    content::configure(output/"content");
    const auto type=graph.inputs()[0].tensorType();fp32(type);need(shape(type,{1,180,60}),"Host capture input shape differs");
    Tensor last;std::vector<char> last_bytes;
    for(uint64_t pass=0;pass<2;++pass) {
        std::vector<float> values(10800);
        for(size_t i=0;i<values.size();++i)values[i]=float(i%127)/16.f-4.f+float(pass)/8.f;
        values[0]=pass==0?-0.f:0.f;
        std::vector<char> expected(values.size()*4);std::memcpy(expected.data(),values.data(),expected.size());
        auto input=Tensor(type).mallocOn(HostDevice::MemRegion());input.write(0,expected.data(),expected.size());
        content::set_context(100+pass,pass,"HOST_SMOKE_"+std::to_string(pass));
        content::capture(input,"caller_input",0,0,&expected,input);
        content::capture(input,"input0_output",0,0,&expected,input); // Simulated alias, not a Session.
        last=input;last_bytes=expected;
    }
    auto rejects=[&](auto operation,const std::string& reason) {
        try {operation();}catch(const std::exception& error) {
            need(std::string(error.what()).find(reason)!=std::string::npos,"Unexpected Host diagnostic rejection");return;
        }
        need(false,"Host diagnostic accepted invalid content/storage");
    };
    content::set_context(102,2,"HOST_NEGATIVE");
    auto wrong=last_bytes;wrong[0]=char(static_cast<unsigned char>(wrong[0])^1U);
    rejects([&]{content::capture(last,"expected_mismatch",0,0,&wrong,last);},"differs from current caller tokens");
    rejects([&]{content::capture(Tensor(type),"unallocated",0,0);},"Only allocated Host CPTR");
    auto half=Tensor(xir::TensorType(xir::FloatType::FP16(),{1,180,60},xir::Layout("***"))).mallocOn(HostDevice::MemRegion());
    rejects([&]{content::capture(half,"fp_sixteen",0,0);},"Only FP32");
    auto summary=file(output/"host-content-check.json");
    summary << "{\"status\":\"host_content_paths_passed\",\"rounds\":2,\"positive_records\":4,"
               "\"expected_mismatch_rejected\":true,\"unallocated_rejected\":true,\"FP16_rejected\":true,"
               "\"device_opened\":false,\"session_created\":false}\n";
}


}
