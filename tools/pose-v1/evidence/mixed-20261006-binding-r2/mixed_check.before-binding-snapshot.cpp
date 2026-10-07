// Separate integration candidate. Original inference_check and CPU checker remain unchanged.
#include "mixed_bridge.hpp"
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

namespace fs=std::filesystem;
namespace xir=icraft::xir;
namespace bridge=pose_v1::mixed_candidate;
using namespace icraft::xrt;
using Clock=std::chrono::steady_clock;
static const std::set<int64_t> host_ids={188,192,437,442,582,649};
static const std::vector<std::string> names={"S11_01_308","S11_01_309","S11_01_310"};
static constexpr const char* url="axi://zg330aiu?npu=0x40000000&dma=0x80000000";
static void need(bool yes,const std::string& why) { if(!yes) throw std::runtime_error(why); }
static std::string quote(const std::string& s) {
    std::ostringstream out; out << '"';
    for(unsigned char c:s) {
        if(c=='"' || c=='\\') out << '\\' << c;
        else if(c<32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str()+'"';
}
static std::ofstream file(const fs::path& path,bool binary=false) {
    std::ofstream f(path,std::ios::out|(binary?std::ios::binary:std::ios::openmode(0)));
    need(bool(f),"Cannot save "+path.string()); f.exceptions(std::ios::failbit|std::ios::badbit);
    f << std::setprecision(17); return f;
}
static double ms(Clock::time_point t) { return std::chrono::duration<double,std::milli>(Clock::now()-t).count(); }
static std::vector<char> bytes(const fs::path& path,size_t expected) {
    need(fs::file_size(path)==expected,"Invalid file length: "+path.string());
    std::ifstream f(path,std::ios::binary); std::vector<char> v(expected);
    need(bool(f.read(v.data(),v.size())),"Cannot read "+path.string()); return v;
}
static void write(const fs::path& path,const std::string& data) {
    auto f=file(path,true); f.write(data.data(),data.size());
}
static bool shape(const xir::TensorType& t,std::initializer_list<int64_t> d) {
    return t->shape.size()==d.size() && std::equal(t->shape.begin(),t->shape.end(),d.begin());
}
static void fp32(const xir::TensorType& t) {
    need(t->element_dtype.is<xir::FloatType>() && t->element_dtype.isFP32(),"FP32 contract differs");
}
struct Args {
    std::string mode,graph,raw,inputs,reference,fixtures,output,cases;
    bool hardware=false;
};
static Args parse(int argc,char** argv) {
    need(argc>=2,"Expected a validation mode"); Args a; a.mode=argv[1];
    for(int i=2;i<argc;++i) {
        std::string flag=argv[i];
        if(flag=="--allow-device-init") { need(!a.hardware,"Duplicate hardware flag"); a.hardware=true; continue; }
        need(i+1<argc,"Missing option value: "+flag); std::string v=argv[++i]; std::string* p=nullptr;
        if(flag=="--graph")p=&a.graph; else if(flag=="--raw")p=&a.raw;
        else if(flag=="--inputs")p=&a.inputs; else if(flag=="--reference-tokens")p=&a.reference;
        else if(flag=="--fixtures")p=&a.fixtures; else if(flag=="--output")p=&a.output;
        else if(flag=="--cases")p=&a.cases;
        need(p!=nullptr,"Unknown option: "+flag); need(p->empty(),"Duplicate option: "+flag); *p=v;
    }
    need(std::set<std::string>{"host-check","offline-check","memory-check","apply-check","mixed"}.count(a.mode)>0,"Unknown mode");
    const bool hardware=a.mode=="memory-check" || a.mode=="apply-check" || a.mode=="mixed";
    need(a.hardware==hardware,"Only hardware modes require --allow-device-init");
    need(!a.output.empty(),"New output directory is required");
    if(a.mode=="host-check") need(!a.graph.empty() && !a.fixtures.empty(),"Host fixture paths required");
    else if(a.mode!="memory-check") need(!a.graph.empty() && !a.raw.empty() && !a.inputs.empty() && !a.reference.empty(),"Graph/RAW/raw CSI/reference paths required");
    if(a.mode=="mixed") need(a.cases=="one" || a.cases=="three","Mixed requires --cases one|three");
    else need(a.cases.empty(),"--cases is only valid in mixed mode");
    return a;
}
static void registry(const xir::Network& graph,HostBackend backend,std::ostream& out,const char* phase) {
    for(auto id:host_ids) {
        auto op=graph.getOpById(id);
        out << "{\"phase\":" << quote(phase) << ",\"op_id\":" << id
            << ",\"supported\":" << (backend.isOpSupported(op)?"true":"false")
            << ",\"init\":" << (backend.getInitFunc(op)?"true":"false")
            << ",\"forward\":" << (backend.getForwardFunc(op)?"true":"false") << "}\n";
    }
    out.flush();
}
static void validate_graph(const xir::Network& g) {
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
static void parameters(const xir::Network& g,const fs::path& output) {
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
static Device open_device(const fs::path& output) {
    auto d=Device::Open(url); d.setWaitTime(10000); const auto v=d.version();
    auto report=file(output/"device-version.json"); report << "{\"url\":" << quote(url) << ",\"versions\":{";
    bool first=true; for(const auto& p:std::map<std::string,std::string>(v.begin(),v.end())) {
        if(!first)report << ','; first=false; report << quote(p.first) << ':' << quote(p.second);
    }
    report << "},\"numerical_accepted\":false}\n"; report.close();
    need(v.count("device") && v.at("device")=="25122301" && v.count("icore") && v.at("icore")=="FMSHZGV3TECH-AID - 24160628","Runtime FPGA/icore differs; stop");
    return d;
}
static void memory_check(const Device& device,const fs::path& output) {
    auto region=device.defaultMemRegion();
    need(region.device().same_as(device) && !region.same_as(HostDevice::MemRegion()),"Unconfirmed device data region");
    auto type=xir::TensorType(xir::FloatType::FP32(),{4096},xir::Layout("C"));
    auto left=Tensor(type).mallocOn(region),right=Tensor(type).mallocOn(region);
    for(const auto& t:{left,right})need(t.data().ptype()==PtrType::ADDR || t.data().ptype()==PtrType::BOTH,"Device data memory has no confirmed physical pointer");
    auto a=left.data().addr(),b=right.data().addr();
    need(a<b ? b-a>=16384 : a-b>=16384,"SDK allocations overlap");
    auto meta=file(output/"memory-region.json"); meta << "{\"left\":";bridge::tensor_info(meta,left);
    meta << ",\"right\":";bridge::tensor_info(meta,right);meta << "}\n";
    for(int pass=0;pass<3;++pass) {
        std::vector<float> x(4096),y(4096);
        for(size_t i=0;i<x.size();++i){x[i]=float(i)-2048.f+float(pass)/8.f;y[i]=2047.f-float(i)-float(pass)/16.f;}
        x[0]=-0.f; y[0]=0.f;
        auto hx=Tensor(type).mallocOn(HostDevice::MemRegion()),hy=Tensor(type).mallocOn(HostDevice::MemRegion());
        hx.write(0,reinterpret_cast<char*>(x.data()),16384);hy.write(0,reinterpret_cast<char*>(y.data()),16384);
        left.copyFrom(0,hx,0,16384);right.copyFrom(0,hy,0,16384);
        auto ax=Tensor(type).mallocOn(HostDevice::MemRegion()),ay=Tensor(type).mallocOn(HostDevice::MemRegion());
        ax.copyFrom(0,left,0,16384);ay.copyFrom(0,right,0,16384);
        std::vector<float> rx(4096),ry(4096);ax.read(reinterpret_cast<char*>(rx.data()),0,16384);ay.read(reinterpret_cast<char*>(ry.data()),0,16384);
        need(std::memcmp(x.data(),rx.data(),16384)==0 && std::memcmp(y.data(),ry.data(),16384)==0,"SDK memory roundtrip mismatch");
        write(output/("memory-pass"+std::to_string(pass)+".left.f32"),std::string(reinterpret_cast<char*>(rx.data()),16384));
        write(output/("memory-pass"+std::to_string(pass)+".right.f32"),std::string(reinterpret_cast<char*>(ry.data()),16384));
    }
}
static std::string dump(const Tensor& t,size_t count) {
    std::ostringstream s(std::ios::out|std::ios::binary);t.dump(s,"SFB");auto raw=s.str();
    need(raw.size()==count*4,"Logical output length differs");
    for(size_t i=0;i<count;++i){float f;std::memcpy(&f,raw.data()+i*4,4);need(std::isfinite(f),"Non-finite model output");}
    return raw;
}
static int run(const Args& a) {
    uint16_t little=1;need(sizeof(float)==4 && *reinterpret_cast<char*>(&little)==1,"Requires little-endian FP32");
    need(!fs::exists(a.output),"Preserve earlier output");fs::create_directories(a.output);const fs::path output=a.output;
    auto stages=file(output/"stages.jsonl");auto mark=[&](const char* s){stages << "{\"stage\":" << quote(s) << "}\n";stages.flush();};
    auto config=file(output/"run-config.json");config << "{\"mode\":" << quote(a.mode) << ",\"cases\":" << quote(a.cases)
        << ",\"device_init_allowed\":" << (a.hardware?"true":"false") << ",\"sdk_wait_ms\":10000,\"numerical_acceptance\":\"pending_reference_comparison\"}\n";config.close();
    auto trace=file(output/"bridge.jsonl");bridge::configure(&trace,false);mark("started");
    try {
        if(a.mode=="host-check") {
            std::vector<std::string> values={"pose_mixed_check","--graph",a.graph,"--fixtures",a.fixtures,"--output",(output/"host").string()};
            std::vector<char*> argv;for(auto& v:values)argv.push_back(v.data());
            need(mixed_host_check(int(argv.size()),argv.data())==0,"Host bridge regression failed");mark("host_bridge_regression_completed");return 0;
        }
        if(a.mode=="memory-check") {
            mark("opening_device_not_readonly");auto d=open_device(output);bridge::configure(&trace,true,d);
            memory_check(d,output);mark("sdk_memory_roundtrip_completed_not_NPU_coherence_proof");return 0;
        }
        auto graph=xir::Network::CreateFromJsonFile(a.graph);validate_graph(graph);
        graph.lazyLoadParamsFromFile(a.raw);parameters(graph,output);mark("real_parameters_validated");
        std::vector<pose_v1::Window> windows;std::vector<pose_v1::Tokens> tokens;
        size_t seen=0;for(const auto& entry:fs::directory_iterator(a.inputs))if(entry.is_regular_file() && entry.path().extension()==".csi")++seen;
        need(seen==3,"Only the fixed three raw windows are allowed");
        for(size_t i=0;i<names.size();++i) {
            auto w=pose_v1::read_window((fs::path(a.inputs)/(names[i]+".csi")).string());
            need(w.frame_id==6+i && w.source_time_ns==0,"Frame identity changed");
            for(const auto& v:w.csi)need(std::isfinite(v.real()) && std::isfinite(v.imag()),"Non-finite raw CSI");
            auto start=Clock::now();auto t=pose_v1::preprocess(w.csi);
            const double preprocess_ms=ms(start);
            for(float v:t)need(std::isfinite(v),"Non-finite tokens");
            auto reference=bytes(fs::path(a.reference)/(names[i]+".input.f32"),t.size()*4);
            need(std::memcmp(t.data(),reference.data(),reference.size())==0,"Board preprocessing differs from fixed reference");
            pose_v1::write_tokens((output/(names[i]+".input.f32")).string(),t);
            auto p=file(output/(names[i]+".preprocess.json"));p << "{\"frame_id\":" << w.frame_id << ",\"preprocess_ms\":" << preprocess_ms << ",\"input_bitwise_equal\":true}\n";
            windows.push_back(w);tokens.push_back(t);
        }
        auto host=HostBackend::Init();auto reg=file(output/"registry.jsonl");registry(graph,host,reg,"before");
        bridge::register_ops(graph,host);registry(graph,host,reg,"after");mark("registered_before_session");
        if(a.mode=="offline-check"){mark("offline_validation_completed");return 0;}
        mark("opening_device_not_readonly");auto device=open_device(output);bridge::configure(&trace,true,device);
        const auto init=Clock::now();
        auto session=Session::Create<zg330::ZG330Backend,HostBackend>(graph.view(),{device,HostDevice::Default()});
        session.enableTimeProfile(true);session.apply();mark("session_applied");
        const double init_ms=ms(init);auto bindings=session.backendBindings();auto bind=file(output/"bindings.jsonl");
        size_t bound_hard=0;
        for(const auto& op:graph->ops) {
            auto it=bindings.find(op->op_id);
            need(it!=bindings.end(),"Original op lacks traceable backend binding (including any fusion): "+std::to_string(op->op_id));
            bind << "{\"op_id\":" << op->op_id << ",\"operator\":" << quote(std::string(op->typeKey()))
                 << ",\"backend\":" << quote(std::string(it->second->typeKey())) << "}\n";
            if(op.is<xir::HardOp>()){need(it->second.is<zg330::ZG330Backend>(),"HardOp left ZG backend");++bound_hard;}
            if(host_ids.count(op->op_id))need(it->second.is<HostBackend>(),"Required CPU node not on Host");
        }
        need(bound_hard==1173,"HardOp binding coverage differs");bind.close();
        if(a.mode=="apply-check"){mark("apply_and_bindings_completed_no_forward");return 0;}
        auto execution=file(output/"operator-execution.jsonl"),results=file(output/"results.jsonl");
        std::set<int64_t> observed;size_t zg_count=0;uint64_t frame=0,invocation=0;std::mutex callback_mutex;
        session.setPostCallBack([&](const Session&,const xir::Operation& op,const Backend& backend,std::vector<Tensor>& out) {
            std::lock_guard<std::mutex> lock(callback_mutex);
            if(backend.is<HostBackend>())observed.insert(op->op_id);
            if(backend.is<zg330::ZG330Backend>())++zg_count;
            execution << "{\"frame_id\":" << frame << ",\"invocation\":" << invocation << ",\"op_id\":" << op->op_id << ",\"backend\":" << quote(std::string(backend->typeKey())) << ",\"outputs\":[";
            for(size_t i=0;i<out.size();++i){if(i)execution << ',';bridge::tensor_info(execution,out[i]);}
            execution << "]}\n";
        });
        std::set<std::string> signatures;
        const size_t count=a.cases=="one"?1:3;
        std::string first_scores,first_poses;
        const size_t calls=count==3?4:1;
        for(size_t call=0;call<calls;++call) {
            const bool repeat=call==3;
            const size_t i=repeat?0:call;
            const std::string stem=names[i]+(repeat?".repeat":"");
            observed.clear();zg_count=0;frame=windows[i].frame_id;invocation=call;bridge::set_frame(frame);
            auto start=Clock::now();Tensor input(graph.inputs()[0]);input.mallocOn(HostDevice::MemRegion());
            input.write(0,reinterpret_cast<char*>(tokens[i].data()),tokens[i].size()*4);
            mark("forward_started");auto forward_start=Clock::now();auto out=session.forward({input});double forward_ms=ms(forward_start);
            execution.flush();need(out.size()==2,"Model output count differs");
            need(shape(out[0].dtype(),{1,100}) && shape(out[1].dtype(),{1,100,14,3}),"Runtime output shape differs");
            for(auto id:host_ids)need(observed.count(id)>0,"Missing Host execution: "+std::to_string(id));
            need(zg_count>0,"No actual ZG callback");
            auto dump_start=Clock::now();auto scores=dump(out[0],100),poses=dump(out[1],4200);double output_ms=ms(dump_start);
            write(output/(stem+".scores.f32"),scores);write(output/(stem+".poses.f32"),poses);
            if(!repeat)signatures.insert(scores+poses);
            if(call==0){first_scores=scores;first_poses=poses;}
            if(repeat)need(scores==first_scores && poses==first_poses,"Repeated first result differs within the same Session");
            std::vector<float> s(100);std::memcpy(s.data(),scores.data(),scores.size());auto best=std::max_element(s.begin(),s.end())-s.begin();
            auto repeat_record=repeat?file(output/"repeat-first.json"):std::ofstream{};
            std::ostream& row=repeat?static_cast<std::ostream&>(repeat_record):static_cast<std::ostream&>(results);
            row << "{\"case\":" << quote(names[i]) << ",\"frame_id\":" << frame << ",\"invocation\":" << invocation << ",\"source_time_ns\":0,\"mode\":\"mixed\",\"top_index\":" << best
                    << ",\"top_score\":" << s[best] << ",\"forward_ms\":" << forward_ms << ",\"output_dump_ms\":" << output_ms
                    << ",\"case_wall_ms_including_evidence_io\":" << ms(start) << ",\"session_init_ms\":" << init_ms << ",\"observed_zg_callbacks\":" << zg_count
                    << ",\"repeated_first_within_session\":" << (repeat?"true":"false")
                    << ",\"numerical_acceptance\":\"pending_ONNX_comparison_and_tolerance_discussion\"}\n";row.flush();
            auto times=file(output/(stem+".sdk-time-profile.jsonl"));
            for(const auto& p:session.timeProfileResults()) {
                need(std::isfinite(std::get<0>(p.second)) && std::isfinite(std::get<1>(p.second)) && std::isfinite(std::get<2>(p.second)) && std::isfinite(std::get<3>(p.second)),"Invalid profile");
                times << "{\"op_id\":" << p.first << ",\"wall\":" << std::get<0>(p.second) << ",\"copy\":" << std::get<1>(p.second)
                      << ",\"hardware\":" << std::get<2>(p.second) << ",\"other\":" << std::get<3>(p.second) << ",\"unit\":\"SDK_raw_unconfirmed\"}\n";
            }
            mark("case_completed");
        }
        session.setPostCallBack(Session::CallBackFunc{});
        if(count==3)need(signatures.size()>1,"All outputs identical for distinct CSI; review needed");
        auto summary=file(output/"summary.json");summary << "{\"status\":\"mixed_engineering_completed\",\"cases\":" << count
            << ",\"forward_calls\":" << calls << ",\"repeated_first_within_session\":" << (count==3?"true":"false")
            << ",\"bound_hard_ops\":1173,\"host_nodes_executed\":6,\"numerical_accepted\":false,\"performance_accepted\":false}\n";
        mark("mixed_completed_not_numerically_accepted");return 0;
    } catch(const std::exception& error) {
        auto failure=file(output/"failure.json");failure << "{\"error\":" << quote(error.what()) << ",\"status\":\"failed_stop_no_retry\"}\n";
        mark("failed_stop_no_retry");throw;
    }
}
int main(int argc,char** argv) {
    try{return run(parse(argc,argv));}catch(const std::exception& e){std::cerr << "STOP: " << e.what() << '\n';return 1;}
}
