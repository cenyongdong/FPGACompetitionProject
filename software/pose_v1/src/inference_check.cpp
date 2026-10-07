// Prepared against installed Icraft 3.39.0 headers; user compilation/run pending.
// No reset/check, HDMI, camera, startup modification, retries or CPU fallback.
#include "preprocess.hpp"
#include <icraft-xir/core/network.h>
#include <icraft-xrt/core/session.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-backends/hostbackend/backend.h>
#ifdef POSE_ENABLE_ZG330
#include <icraft-backends/zg330backend/zg330backend.h>
#endif
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
#include <stdexcept>
#include <tuple>
#include <vector>

namespace fs = std::filesystem;
using namespace icraft::xrt;
using icraft::xir::FloatType;
using icraft::xir::TensorType;
using Clock = std::chrono::steady_clock;
static constexpr const char* kUrl = "axi://zg330aiu?npu=0x40000000&dma=0x80000000";
static const std::set<int64_t> kHostIds = {188,192,437,442,582,649};
static const std::set<std::string> kCaseNames = {"S11_01_308","S11_01_309","S11_01_310"};

static void require(bool yes, const std::string& message) {
    if (!yes) throw std::runtime_error(message);
}
static double elapsed(Clock::time_point begin) {
    return std::chrono::duration<double, std::milli>(Clock::now()-begin).count();
}
static std::string quote(const std::string& s) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : s) {
        if (c=='"' || c=='\\') out << '\\' << c;
        else if (c<32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str()+'"';
}
static std::ofstream file(const fs::path& path, bool binary=false) {
    std::ofstream out(path, std::ios::out | (binary ? std::ios::binary : std::ios::openmode(0)));
    require(bool(out), "Cannot create " + path.string());
    out.exceptions(std::ios::failbit | std::ios::badbit);
    out << std::setprecision(17);
    return out;
}
static bool shapeIs(const TensorType& type, std::initializer_list<int64_t> dims) {
    if (type->shape.size()!=dims.size()) return false;
    size_t i=0;
    for (auto d : dims) if (type->shape[i++]!=d) return false;
    return true;
}
static void fp32(const TensorType& type) {
    require(type->element_dtype.is<FloatType>(), "Expected unquantized floating-point I/O");
    auto sem = type->element_dtype.cast<FloatType>().semantics();
    require(sem.bits==32 && sem.precision==24 && sem.emax==127 && sem.emin==-126,
            "Expected IEEE float32 I/O");
}
static void writeType(std::ostream& out, const TensorType& type) {
    out << "{\"element_type\":" << quote(std::string(type->element_dtype->typeKey())) << ",\"shape\":[";
    for (size_t i=0;i<type->shape.size();++i) { if(i) out << ','; out << type->shape[i]; }
    out << "],\"layout_type\":" << quote(std::string(type->layout->typeKey()))
        << ",\"merged_distribution_count\":" << type->merged_distrs.size() << '}';
}
static void graphIO(const icraft::xir::Network& network, const fs::path& dest) {
    auto inputs=network.inputs(), outputs=network.outputs();
    require(inputs.size()==1 && outputs.size()==2, "Expected one input and two outputs");
    fp32(inputs[0].tensorType());
    require(shapeIs(inputs[0].tensorType(), {1,180,60}), "Unexpected input shape");
    fp32(outputs[0].tensorType()); fp32(outputs[1].tensorType());
    require(shapeIs(outputs[0].tensorType(), {1,100}) && shapeIs(outputs[1].tensorType(), {1,100,14,3}),
            "Unexpected output order/shape; do not guess a remapping");
    auto out=file(dest);
    out << "{\"input\":"; writeType(out, inputs[0].tensorType());
    out << ",\"scores\":"; writeType(out, outputs[0].tensorType());
    out << ",\"poses\":"; writeType(out, outputs[1].tensorType()); out << "}\n";
}
static std::vector<float> dumpOutput(const Tensor& tensor, size_t count, const fs::path& path) {
    // SFB removes hardware layout/padding and yields logical software float binary.
    std::ostringstream bytes(std::ios::out | std::ios::binary);
    tensor.dump(bytes, "SFB");
    const auto data=bytes.str();
    require(data.size()==count*sizeof(float), "SFB output byte count differs from logical shape");
    std::vector<float> values(count);
    std::memcpy(values.data(), data.data(), data.size());
    for (float value : values) require(std::isfinite(value), "Non-finite model output");
    auto out=file(path, true); out.write(data.data(), data.size());
    return values;
}
static void deviceVersion(const Device& device, const fs::path& path) {
    auto report=file(path);
    auto versions=device.version();
    std::map<std::string,std::string> sorted(versions.begin(),versions.end());
    report << "{\"url\":" << quote(kUrl) << ",\"versions\":{";
    bool first=true;
    for(const auto& pair : sorted) { if(!first) report << ','; first=false; report << quote(pair.first) << ':' << quote(pair.second); }
    report << "},\"compatibility_passed\":false}\n";
}
struct Args {
    std::string mode, graph, raw, input_dir, output_dir, reference_dir;
    bool permit_device=false;
};
static Args parse(int argc, char** argv) {
    require(argc>=2, "Usage: pose_inference_check inspect|probe|host|mixed --output NEW_DIR [--graph JSON --raw RAW --inputs DIR] [--allow-device-init]");
    Args a; a.mode=argv[1];
    for (int i=2;i<argc;++i) {
        std::string flag=argv[i];
        if (flag=="--allow-device-init") { require(!a.permit_device,"Duplicate flag"); a.permit_device=true; continue; }
        require(i+1<argc, "Missing argument for "+flag);
        std::string value=argv[++i];
        std::string* target=nullptr;
        if(flag=="--graph") target=&a.graph;
        else if(flag=="--raw") target=&a.raw;
        else if(flag=="--inputs") target=&a.input_dir;
        else if(flag=="--output") target=&a.output_dir;
        else if(flag=="--reference-tokens") target=&a.reference_dir;
        require(target!=nullptr, "Unknown option "+flag);
        require(target->empty(), "Duplicate option "+flag); *target=value;
    }
    require(a.mode=="inspect" || a.mode=="probe" || a.mode=="host" || a.mode=="mixed", "Unknown mode");
    require(!a.output_dir.empty(), "Output directory is required");
    bool hardware=a.mode=="probe" || a.mode=="mixed";
    require(hardware==a.permit_device, "Hardware modes require --allow-device-init; offline modes reject it");
    if(a.mode!="probe") require(!a.graph.empty(), "Graph is required");
    if(a.mode=="host" || a.mode=="mixed") require(!a.raw.empty() && !a.input_dir.empty(), "Raw parameters and inputs are required");
    require(a.reference_dir.empty() || a.mode=="host", "Reference tokens are only allowed for the Host comparison, never board mixed inference");
#ifndef POSE_ENABLE_ZG330
    require(!hardware, "This Host-only binary has no hardware backend");
#endif
    return a;
}
static int run(const Args& a) {
    uint16_t little=1;
    static_assert(sizeof(float)==4,"float must be 32 bit");
    require(*reinterpret_cast<char*>(&little)==1, "Only little-endian targets are supported");
    require(!fs::exists(a.output_dir), "Output directory already exists; preserve earlier evidence");
    require(fs::create_directories(a.output_dir), "Cannot create output directory");
    const fs::path output=a.output_dir;
    auto stage=file(output/"stages.jsonl");
    auto mark=[&](const char* name) { stage << "{\"stage\":" << quote(name) << "}\n"; stage.flush(); };
    mark("started");
    try {
        auto config=file(output/"run-config.json");
        config << "{\"mode\":" << quote(a.mode) << ",\"graph_path\":" << quote(a.graph)
               << ",\"parameter_path\":" << quote(a.raw) << ",\"input_directory\":" << quote(a.input_dir)
               << ",\"reference_token_directory\":" << quote(a.reference_dir)
               << ",\"device_init_allowed\":" << (a.permit_device?"true":"false")
               << ",\"sdk_tensor_wait_ms\":10000,\"ZG_optimization\":\"SDK_defaults_unchanged\"}\n";
        config.close();
        std::vector<fs::path> windows;
        std::vector<pose_v1::Window> loaded;
        if(a.mode=="host" || a.mode=="mixed") {
            for(const auto& entry : fs::directory_iterator(a.input_dir))
                if(entry.is_regular_file() && entry.path().extension()==".csi") windows.push_back(entry.path());
            std::sort(windows.begin(),windows.end());
            require(windows.size()==3,"Initial gate requires exactly three fixed .csi windows");
            std::set<uint64_t> frame_ids;
            std::set<std::string> case_names;
            for(const auto& path : windows) {
                case_names.insert(path.stem().string());
                loaded.push_back(pose_v1::read_window(path.string()));
                require(frame_ids.insert(loaded.back().frame_id).second, "Duplicate frame id");
                for(const auto& value : loaded.back().csi)
                    require(std::isfinite(value.real()) && std::isfinite(value.imag()),"Non-finite raw CSI before device access");
            }
            require(case_names==kCaseNames,"Initial gate only permits the approved three regression cases");
            mark("inputs_validated_before_device_access");
        }
        if(a.mode=="probe") {
#ifdef POSE_ENABLE_ZG330
            mark("opening_device_not_readonly");
            auto device=Device::Open(kUrl);
            deviceVersion(device,output/"device-version.json");
            mark("probe_complete_requires_review");
#endif
            return 0;
        }
        auto network=icraft::xir::Network::CreateFromJsonFile(a.graph);
        graphIO(network,output/"graph-io.json");
        if(a.mode=="inspect") { mark("offline_inspection_complete"); return 0; }
        network.lazyLoadParamsFromFile(a.raw);
        mark("parameters_loaded");
        // Host reference cannot accept compiled ZG HardOps as a CPU substitute.
        if(a.mode=="host") for(const auto& op : network->ops)
            require(std::string(op->typeKey())!="icraft::xir::HardOp", "Host reference must use the optimized graph, not the ZG graph");
        Session session;
        Device device;
        const auto init_start=Clock::now();
        if(a.mode=="host") session=Session::Create<HostBackend>(network.view(),{HostDevice::Default()});
        else {
#ifdef POSE_ENABLE_ZG330
            mark("opening_device_not_readonly");
            device=Device::Open(kUrl); device.setWaitTime(10000);
            deviceVersion(device,output/"device-version.json");
            session=Session::Create<zg330::ZG330Backend,HostBackend>(network.view(),{device,HostDevice::Default()});
#endif
        }
        session.enableTimeProfile(true);
        session.apply();
        const double init_ms=elapsed(init_start);
        mark("session_applied");
        auto bindings=session.backendBindings();
        auto binding_file=file(output/"backend-bindings.jsonl");
        std::map<int64_t,Backend> sorted_bindings(bindings.begin(),bindings.end());
        for(const auto& pair : sorted_bindings)
            binding_file << "{\"op_id\":" << pair.first << ",\"backend\":" << quote(std::string(pair.second->typeKey())) << "}\n";
        if(a.mode=="mixed") for(auto id : kHostIds) {
            auto found=bindings.find(id);
            require(found!=bindings.end() && found->second.is<HostBackend>(), "Required Host operator not bound to HostBackend: "+std::to_string(id));
        }
        auto execution=file(output/"operator-execution.jsonl");
        std::mutex callback_mutex;
        std::set<int64_t> observed_host;
        size_t observed_zg=0;
        uint64_t current_frame=0;
        session.setPostCallBack([&](const Session&,const icraft::xir::Operation& op,const Backend& backend,std::vector<Tensor>&) {
            std::lock_guard<std::mutex> guard(callback_mutex);
            if(backend.is<HostBackend>()) observed_host.insert(op->op_id);
#ifdef POSE_ENABLE_ZG330
            if(backend.is<zg330::ZG330Backend>()) ++observed_zg;
#endif
            execution << "{\"frame_id\":" << current_frame << ",\"op_id\":" << op->op_id
                      << ",\"operator\":" << quote(std::string(op->typeKey()))
                      << ",\"backend\":" << quote(std::string(backend->typeKey())) << "}\n";
        });
        auto results=file(output/"results.jsonl");
        for(size_t index=0;index<windows.size();++index) {
            observed_host.clear(); observed_zg=0; current_frame=loaded[index].frame_id;
            const auto case_start=Clock::now(), pre_start=case_start;
            auto tokens=pose_v1::Tokens{};
            const auto stem=windows[index].stem().string();
            if(a.reference_dir.empty()) tokens=pose_v1::preprocess(loaded[index].csi);
            else {
                const auto token_path=fs::path(a.reference_dir)/(stem+".input.f32");
                require(fs::file_size(token_path)==tokens.size()*sizeof(float), "Reference token byte count is invalid");
                std::ifstream input_file(token_path,std::ios::binary);
                require(bool(input_file.read(reinterpret_cast<char*>(tokens.data()),tokens.size()*sizeof(float))), "Cannot read reference tokens");
            }
            for(float value : tokens) require(std::isfinite(value),"Non-finite preprocessing tensor");
            const double preprocess_ms=elapsed(pre_start);
            pose_v1::write_tokens((output/(stem+".input.f32")).string(),tokens);
            const auto upload_start=Clock::now();
            Tensor input(network.inputs()[0]);
            input.mallocOn(HostDevice::MemRegion());
            input.write(0,reinterpret_cast<char*>(tokens.data()),tokens.size()*sizeof(float));
            const double input_ms=elapsed(upload_start);
            mark("forward_started");
            const auto forward_start=Clock::now();
            auto tensors=session.forward({input});
            const double forward_ms=elapsed(forward_start);
            execution.flush();
            require(tensors.size()==2,"Model returned unexpected output count");
            require(shapeIs(tensors[0].dtype(),{1,100}) && shapeIs(tensors[1].dtype(),{1,100,14,3}),"Runtime output shape differs from graph");
            if(a.mode=="mixed") {
                for(auto id : kHostIds) require(observed_host.count(id)!=0,"No observed execution for required Host operator "+std::to_string(id));
                require(observed_zg>0,"No observed ZG330 backend execution");
            }
            const auto dump_start=Clock::now();
            auto scores=dumpOutput(tensors[0],100,output/(stem+".scores.f32"));
            dumpOutput(tensors[1],4200,output/(stem+".poses.f32"));
            const double output_ms=elapsed(dump_start);
            const size_t best=std::max_element(scores.begin(),scores.end())-scores.begin();
            results << "{\"case\":" << quote(stem) << ",\"frame_id\":" << current_frame
                    << ",\"source_time_ns\":" << loaded[index].source_time_ns << ",\"mode\":" << quote(a.mode)
                    << ",\"tensor_source\":" << quote(a.reference_dir.empty()?"raw_CSI_preprocessing":"fixed_reference_tokens_Host_only")
                    << ",\"top_index\":" << best << ",\"top_score\":" << scores[best]
                    << ",\"preprocess_ms\":" << preprocess_ms << ",\"host_input_copy_ms\":" << input_ms
                    << ",\"forward_ms\":" << forward_ms << ",\"output_dump_ms\":" << output_ms
                    << ",\"case_wall_ms_including_evidence_io\":" << elapsed(case_start)
                    << ",\"session_init_ms\":" << init_ms << ",\"observed_zg_callbacks\":" << observed_zg
                    << ",\"numerical_acceptance\":\"pending_comparison_and_review\"}\n";
            results.flush();
            auto times=file(output/(stem+".sdk-time-profile.jsonl"));
            for(const auto& pair : session.timeProfileResults()) {
                require(std::isfinite(std::get<0>(pair.second)) && std::isfinite(std::get<1>(pair.second)) &&
                        std::isfinite(std::get<2>(pair.second)) && std::isfinite(std::get<3>(pair.second)),"Non-finite SDK time profile");
                times << "{\"op_id\":" << pair.first << ",\"wall\":" << std::get<0>(pair.second)
                      << ",\"copy\":" << std::get<1>(pair.second) << ",\"hardware\":" << std::get<2>(pair.second)
                      << ",\"other\":" << std::get<3>(pair.second) << ",\"unit\":\"SDK_raw_unconfirmed\"}\n";
            }
            mark("case_completed");
        }
        session.setPostCallBack(Session::CallBackFunc{});
        mark("three_cases_completed_not_numerically_accepted");
        return 0;
    } catch(const std::exception& error) {
        auto failure=file(output/"failure.json");
        failure << "{\"error\":" << quote(error.what()) << ",\"passed\":false}\n";
        mark("failed_stop_no_retry"); throw;
    }
}
int main(int argc,char** argv) {
    try { return run(parse(argc,argv)); }
    catch(const std::exception& error) { std::cerr << "STOP: " << error.what() << '\n'; return 1; }
}
