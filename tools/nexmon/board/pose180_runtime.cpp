#include "pose180_runtime.hpp"
#include <icraft-backends/zg330backend/zg330backend.h>
#include <icraft-backends/hostbackend/backend.h>
#include <icraft-xir/ops/ops.h>
#include <icraft-xrt/core/session.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xrt/dev/zg330_device.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace nexmon_board {
namespace {
namespace fs = std::filesystem;
namespace xir = icraft::xir;
using namespace icraft::xrt;
using Clock = std::chrono::steady_clock;
static_assert(sizeof(float) == 4, "The existing FP32 archive requires 4-byte floats");

void require(bool yes, const std::string& message) {
    if (!yes) throw std::runtime_error(message);
}

double elapsed(Clock::time_point begin) {
    return std::chrono::duration<double,std::milli>(Clock::now()-begin).count();
}

std::string json_quote(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4)
                             << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str()+'"';
}

void bytes_file(const fs::path& path, const char* bytes, std::size_t size) {
    std::ofstream out(path,std::ios::binary);
    require(bool(out),"Cannot open evidence " + path.string());
    out.write(bytes,static_cast<std::streamsize>(size));
    out.flush();
    require(bool(out),"Cannot preserve evidence " + path.string());
}

void text_file(const fs::path& path, const std::string& value) {
    bytes_file(path,value.data(),value.size());
}

bool shape(const xir::TensorType& dtype, std::initializer_list<int64_t> expected) {
    return dtype->element_dtype.isFP32() && dtype->shape.size() == expected.size()
        && std::equal(dtype->shape.begin(),dtype->shape.end(),expected.begin());
}

// The same actual SDK ownership/completion checks as pose180_validate. The
// final completion count comes from applied runtime fusion, never an old graph.
uint32_t validate_fusion(const Session& session, const xir::Network& graph,
                         const fs::path& output) {
    std::set<int64_t> originals,covered;
    for (const auto& op : graph->ops)
        if (op.is<xir::HardOp>()) originals.insert(op->op_id);
    std::map<int,int> spans;
    std::ofstream evidence(output/"fusion.jsonl");
    require(bool(evidence),"Cannot open fusion evidence");
    auto bindings = session.backendBindings();
    std::size_t groups = 0,host_ports = 0;
    for (const auto& item : bindings) {
        if (item.second.is<HostBackend>()) {
            auto op = graph.getOpById(item.first);
            require(op.is<xir::Input>() || op.is<xir::Output>(),
                    "Unexpected Host compute binding");
            ++host_ports;
            continue;
        }
        require(item.second.is<zg330::ZG330Backend>(),"Unexpected backend binding");
        auto info = item.second.cast<zg330::ZG330Backend>()->forward_info;
        require(info.defined(),"Missing actual ZG metadata");
        auto found = info->hardop_map.find(item.first);
        require(found != info->hardop_map.end() && found->second.defined(),
                "Missing fused member metadata");
        auto entry = found->second;
        require(entry->net_hardop.defined() && entry->net_hardop->op_id == item.first,
                "Fused node identity differs");
        auto sync = info->idx_map.find(item.first);
        require(sync != info->idx_map.end() && sync->second == entry->sync_idx,
                "Completion metadata differs");
        require(sync->second.first >= 0 && sync->second.second > 0
                && spans.emplace(sync->second).second,
                "Invalid or repeated completion interval");
        std::vector<int64_t> members(entry->merge_from.begin(),entry->merge_from.end());
        if (members.empty()) members.push_back(item.first);
        evidence << "{\"group\":" << item.first << ",\"sync_start\":"
                 << sync->second.first << ",\"layer_count\":" << sync->second.second
                 << ",\"members\":[";
        for (std::size_t i=0;i<members.size();++i) {
            if (i) evidence << ',';
            evidence << members[i];
            require(originals.count(members[i]) && covered.insert(members[i]).second,
                    "Invalid/repeated original HardOp member");
        }
        evidence << "]}\n";
        ++groups;
    }
    evidence.flush();
    require(bool(evidence),"Cannot preserve fusion evidence");
    require(covered == originals && host_ports == 2 && groups > 0,
            "Incomplete graph ownership");
    uint32_t next = 0;
    for (const auto& span : spans) {
        require(uint32_t(span.first) == next,
                "Gap or overlap in runtime completion intervals");
        next += uint32_t(span.second);
    }
    require(next > 0 && next < 100000,"Invalid final completion count");
    text_file(output/"fusion-summary.json","{\"hardops\":"+
        std::to_string(originals.size())+",\"groups\":"+std::to_string(groups)+
        ",\"host_compute\":0,\"host_ports\":2,\"final_count\":"+
        std::to_string(next)+",\"coverage_complete\":true}\n");
    return next;
}

std::string dump(const Tensor& tensor, std::size_t count,
                 const fs::path& partial_path) {
    std::ostringstream stream(std::ios::out|std::ios::binary);
    try {
        tensor.dump(stream,"SFB");
    } catch (...) {
        // Best effort only: an evidence I/O error must not replace SDK failure.
        try { text_file(partial_path,stream.str()); } catch (...) {}
        throw;
    }
    auto data = stream.str();
    if (data.size() != count*sizeof(float)) {
        text_file(partial_path,data);
        throw std::runtime_error("Actual output length differs");
    }
    return data;
}
} // namespace

struct Pose180Runtime::Impl {
    fs::path output;
    // Handles are destroyed in reverse order: tensor, Session, Device, graph.
    xir::Network graph;
    Device device;
    Session session;
    Tensor input_tensor;
    uint32_t final_count = 0;
    uint64_t npu_calls = 0,host_compute_calls = 0,next_invocation = 0;
    bool failed = false;

    Impl(const std::string& package_directory,const std::string& evidence_directory)
        : output(evidence_directory) {
        // Never overwrite a previous invocation's input or first outputs.
        require(fs::create_directory(output),"Preserve existing output directory");
        const auto initializing = Clock::now();
        try {
            const fs::path root(package_directory);
            graph = xir::Network::CreateFromJsonFile(
                (root/"models/piw24_pose180_ZG.json").string());
            require(graph->icraft_version == "v3.39.0" && !graph->swap_mode,
                    "Graph version/swap differs");
            auto in = graph.inputs(),out = graph.outputs();
            require(in.size() == 1 && out.size() == 2
                    && shape(in[0].tensorType(),{1,180,60})
                    && shape(out[0].tensorType(),{1,180})
                    && shape(out[1].tensorType(),{1,180,14,3}),
                    "180-query graph ports differ");
            for (const auto& op : graph->ops)
                require(op.is<xir::HardOp>() || op.is<xir::Input>()
                        || op.is<xir::Output>(),"Host compute/TopK remains");
            graph.lazyLoadParamsFromFile((root/"models/piw24_pose180_ZG.raw").string());
            device = Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000");
            device.setWaitTime(10000);
            auto version = device.version();
            require(version.count("device") && version.at("device") == "25122301"
                    && version.count("icore")
                    && version.at("icore") == "FMSHZGV3TECH-AID - 24160628",
                    "Actual device/icore identity differs: device="+
                    (version.count("device")?version.at("device"):"<missing>")+
                    "; icore="+(version.count("icore")?version.at("icore"):"<missing>"));
            session = Session::Create<zg330::ZG330Backend,HostBackend>(
                graph.view(),{device,HostDevice::Default()});
            session.enableTimeProfile(false);
            session.apply();
            final_count = validate_fusion(session,graph,output);
            session.setPostCallBack([this](const Session&,const xir::Operation& op,
                                          const Backend& backend,std::vector<Tensor>&) {
                if (backend.is<zg330::ZG330Backend>()) ++npu_calls;
                else if (!op.is<xir::Input>() && !op.is<xir::Output>())
                    ++host_compute_calls;
            });
            input_tensor = Tensor(in[0]).mallocOn(HostDevice::MemRegion());
            text_file(output/"initialized.json","{\"initialization_ms\":"+
                std::to_string(elapsed(initializing))+",\"device\":"+
                json_quote(version.at("device"))+",\"icore\":"+
                json_quote(version.at("icore"))+",\"final_count\":"+
                std::to_string(final_count)+",\"host_compute\":0}\n");
        } catch (const std::exception& e) {
            preserve_failure("initialization",e.what());
            throw;
        } catch (...) {
            preserve_failure("initialization","Non-standard SDK exception");
            throw;
        }
    }

    ~Impl() {
        // No forward, reset, new synchronization or device reopening on exit.
        if (session.defined()) {
            try { session.setPostCallBack(Session::CallBackFunc{}); }
            catch (...) {} // Destructors still release the owning SDK handles.
        }
    }

    void preserve_failure(const std::string& stage,const std::string& message) noexcept {
        failed = true;
        try {
            text_file(output/"failure.json","{\"stage\":"+json_quote(stage)+
                ",\"invocation\":"+std::to_string(next_invocation)+
                ",\"error\":"+json_quote(message)+",\"automatic_retry\":false}\n");
        } catch (...) {} // Keep the original error, including evidence I/O errors.
    }

    Pose180Result infer(const std::array<float,10800>& input) {
        require(!failed,"Runtime stopped after its first failure; automatic retry forbidden");
        const auto start = Clock::now();
        std::ostringstream prefix;
        prefix << "frame-" << std::setw(12) << std::setfill('0') << next_invocation;
        const auto base = output/prefix.str();
        try {
            bytes_file(base.string()+".input.f32",reinterpret_cast<const char*>(input.data()),
                       input.size()*sizeof(float));
            for (float value : input)
                require(std::isfinite(value),"Nonfinite model input; preserve and stop without retry");

            // The SDK write API takes char* even for its source. Keep the
            // caller's input const, using an owned bit-identical source copy.
            auto tensor_input = input;
            input_tensor.write(0,reinterpret_cast<char*>(tensor_input.data()),
                               tensor_input.size()*sizeof(float));
            device.reset(1);
            const auto cleared_count = device.cast<ZG330Device>().layerCount();
            require(cleared_count == 0,
                    "Status-only frame clear did not reach zero: actual="+
                    std::to_string(cleared_count));
            npu_calls = 0;
            host_compute_calls = 0;
            Pose180Result result;
            result.invocation = next_invocation;
            const auto forward_begin = Clock::now();
            auto outputs = session.forward({input_tensor});
            result.timings.forward_ms = elapsed(forward_begin);
            require(outputs.size() == 2,"Runtime output count differs");
            const auto wait_begin = Clock::now();
            for (const auto& tensor : outputs)
                require(tensor.waitForReady(std::chrono::milliseconds(10000)),
                        "Native final output wait failed");
            result.timings.output_wait_ms = elapsed(wait_begin);
            const auto count = device.cast<ZG330Device>().layerCount();
            require(count == final_count,"Runtime final completion count differs: actual="+
                    std::to_string(count)+"; expected="+std::to_string(final_count));
            require(npu_calls > 0 && host_compute_calls == 0,
                    "Unexpected actual Host computation: npu_callbacks="+
                    std::to_string(npu_calls)+"; host_compute_callbacks="+
                    std::to_string(host_compute_calls));

            const auto readback_begin = Clock::now();
            const auto scores = dump(outputs[0],180,base.string()+".scores-partial.bin");
            text_file(base.string()+".scores.f32",scores);
            const auto poses = dump(outputs[1],7560,base.string()+".poses-partial.bin");
            text_file(base.string()+".poses.f32",poses);
            result.timings.readback_ms = elapsed(readback_begin);
            result.timings.process_ms = elapsed(start);
            // All first output bytes are closed/flushed before any finite or
            // candidate checks. Never read late values to repair a failed call.
            std::memcpy(result.scores.data(),scores.data(),scores.size());
            std::memcpy(result.poses.data(),poses.data(),poses.size());
            bool finite = true;
            float best_score = -std::numeric_limits<float>::infinity();
            for (std::size_t i=0;i<result.scores.size();++i) {
                const float value = result.scores[i];
                finite = finite && std::isfinite(value);
                if (value > best_score) { best_score = value; result.best_index = i; }
            }
            for (float value : result.poses) finite = finite && std::isfinite(value);
            std::ostringstream row;
            row << std::setprecision(17)
                << "{\"invocation\":" << result.invocation
                << ",\"input_values\":10800,\"scores\":180,\"pose_values\":7560"
                << ",\"finite\":" << (finite?"true":"false")
                << ",\"completed_layers\":" << count
                << ",\"npu_callbacks\":" << npu_calls << ",\"host_compute_callbacks\":0"
                << ",\"process_ms\":" << result.timings.process_ms
                << ",\"forward_ms\":" << result.timings.forward_ms
                << ",\"output_wait_ms\":" << result.timings.output_wait_ms
                << ",\"readback_ms\":" << result.timings.readback_ms;
            // Nonfinite values are kept in binary, never emitted as invalid JSON.
            if (finite) row << ",\"best_index\":" << result.best_index
                            << ",\"best_score\":" << best_score;
            row << "}\n";
            text_file(base.string()+".json",row.str());
            require(finite,"Nonfinite model output; preserve and stop without retry");
            require(result.best_index < result.scores.size(),"Invalid candidate index");
            ++next_invocation;
            return result;
        } catch (const std::exception& e) {
            preserve_failure("inference",e.what());
            throw;
        } catch (...) {
            preserve_failure("inference","Non-standard SDK exception");
            throw;
        }
    }
};

Pose180Runtime::Pose180Runtime(const std::string& package_directory,
                             const std::string& evidence_directory)
    : impl_(std::make_unique<Impl>(package_directory,evidence_directory)) {}

Pose180Runtime::~Pose180Runtime() = default;

Pose180Result Pose180Runtime::infer(const std::array<float,10800>& input) {
    return impl_->infer(input);
}

} // namespace nexmon_board
