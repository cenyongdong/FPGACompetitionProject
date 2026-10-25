// 独立180候选模型验证：只使用标准输入/输出搬运，不链接TopK/Gather Host桥。
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
#include <iostream>
#include <map>
#include <limits>
#include <set>
#include <sstream>
#include <vector>

namespace fs = std::filesystem;
namespace xir = icraft::xir;
using namespace icraft::xrt;
using Clock = std::chrono::steady_clock;

void require(bool yes, const std::string& message) {
    if (!yes) throw std::runtime_error(message);
}

std::string quoted(const std::string& value) {
    std::ostringstream out;
    out << '"';
    for (unsigned char c : value) {
        if (c == '"' || c == '\\') out << '\\' << c;
        else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str() + '"';
}

double elapsed(Clock::time_point begin) {
    return std::chrono::duration<double, std::milli>(Clock::now()-begin).count();
}

void text_file(const fs::path& path, const std::string& value) {
    std::ofstream out(path, std::ios::binary);
    out.write(value.data(), value.size());
    require(bool(out), "Cannot preserve " + path.string());
}

std::vector<float> read(const fs::path& path, size_t count) {
    require(fs::file_size(path) == count*sizeof(float), "Fixture length differs: " + path.string());
    std::ifstream in(path, std::ios::binary);
    std::vector<float> value(count);
    in.read(reinterpret_cast<char*>(value.data()), value.size()*sizeof(float));
    require(bool(in), "Fixture read failed");
    for (float v : value) require(std::isfinite(v), "Nonfinite fixture");
    return value;
}

bool shape(const xir::TensorType& dtype, std::initializer_list<int64_t> expected) {
    return dtype->element_dtype.isFP32() && dtype->shape.size() == expected.size()
        && std::equal(dtype->shape.begin(), dtype->shape.end(), expected.begin());
}

struct Case {
    std::string name;
    std::vector<float> input, scores, poses;
    Tensor tensor;
};

// 完整追溯实际SDK合并成员及连续完成区间，不套旧模型745/736等计数。
uint32_t validate_fusion(const Session& session, const xir::Network& graph, const fs::path& output) {
    std::set<int64_t> originals, covered;
    for (const auto& op : graph->ops) if (op.is<xir::HardOp>()) originals.insert(op->op_id);
    std::map<int,int> spans;
    std::ofstream evidence(output/"fusion.jsonl");
    auto bindings = session.backendBindings();
    size_t groups = 0, host_ports = 0;
    for (const auto& item : bindings) {
        if (item.second.is<HostBackend>()) {
            auto op = graph.getOpById(item.first);
            require(op.is<xir::Input>() || op.is<xir::Output>(), "Unexpected Host compute binding");
            ++host_ports;
            continue;
        }
        require(item.second.is<zg330::ZG330Backend>(), "Unexpected backend binding");
        auto info = item.second.cast<zg330::ZG330Backend>()->forward_info;
        require(info.defined(), "Missing actual ZG metadata");
        auto found = info->hardop_map.find(item.first);
        require(found != info->hardop_map.end() && found->second.defined(), "Missing fused member metadata");
        auto entry = found->second;
        require(entry->net_hardop.defined() && entry->net_hardop->op_id == item.first, "Fused node identity differs");
        auto sync = info->idx_map.find(item.first);
        require(sync != info->idx_map.end() && sync->second == entry->sync_idx, "Completion metadata differs");
        require(sync->second.first >= 0 && sync->second.second > 0 && spans.emplace(sync->second).second,
                "Invalid or repeated completion interval");
        std::vector<int64_t> members(entry->merge_from.begin(), entry->merge_from.end());
        if (members.empty()) members.push_back(item.first);
        evidence << "{\"group\":" << item.first << ",\"sync_start\":" << sync->second.first
                 << ",\"layer_count\":" << sync->second.second << ",\"members\":[";
        for (size_t i=0; i<members.size(); ++i) {
            if (i) evidence << ',';
            evidence << members[i];
            require(originals.count(members[i]) && covered.insert(members[i]).second, "Invalid/repeated original HardOp member");
        }
        evidence << "]}\n";
        ++groups;
    }
    require(covered == originals && host_ports == 2 && groups > 0, "Incomplete graph ownership");
    uint32_t next = 0;
    for (const auto& span : spans) {
        require(uint32_t(span.first) == next, "Gap or overlap in runtime completion intervals");
        next += uint32_t(span.second);
    }
    require(next > 0 && next < 100000, "Invalid final completion count");
    text_file(output/"fusion-summary.json", "{\"hardops\":"+std::to_string(originals.size())+
              ",\"groups\":"+std::to_string(groups)+",\"host_compute\":0,\"host_ports\":2,\"final_count\":"+
              std::to_string(next)+",\"coverage_complete\":true}\n");
    return next;
}

std::string dump(const Tensor& tensor, size_t count, const fs::path& failure_path) {
    std::ostringstream stream(std::ios::out | std::ios::binary);
    try { tensor.dump(stream, "SFB"); }
    catch (...) { text_file(failure_path, stream.str()); throw; }
    auto data = stream.str();
    if (data.size() != count*sizeof(float)) {
        text_file(failure_path, data);
        throw std::runtime_error("Actual output length differs");
    }
    return data;
}

int main(int argc, char** argv) {
    fs::path output;
    uint64_t completed=0, saved=0;
    try {
        require(argc == 4, "Usage: pose180_validate PACKAGE OUTPUT verify|stress");
        fs::path root=argv[1]; output=argv[2]; const std::string stage=argv[3];
        require(stage == "verify" || stage == "stress", "Unknown stage");
        require(fs::create_directory(output), "Preserve existing output directory");
        std::vector<Case> cases;
        for (const char* name : {"S11_01_308", "S12_03_316", "S13_41_304"}) {
            Case c; c.name=name;
            c.input=read(root/"fixtures"/(c.name+".input.f32"),10800);
            c.scores=read(root/"fixtures"/(c.name+".instruction.scores.f32"),180);
            c.poses=read(root/"fixtures"/(c.name+".instruction.poses.f32"),7560);
            cases.push_back(std::move(c));
        }
        auto initializing=Clock::now();
        {
            auto graph=xir::Network::CreateFromJsonFile((root/"models/piw24_pose180_ZG.json").string());
            require(graph->icraft_version == "v3.39.0" && !graph->swap_mode, "Graph version/swap differs");
            auto in=graph.inputs(), out=graph.outputs();
            require(in.size()==1 && out.size()==2 && shape(in[0].tensorType(),{1,180,60})
                    && shape(out[0].tensorType(),{1,180}) && shape(out[1].tensorType(),{1,180,14,3}), "180-query graph ports differ");
            for (const auto& op : graph->ops)
                require(op.is<xir::HardOp>() || op.is<xir::Input>() || op.is<xir::Output>(), "Host compute/TopK remains");
            graph.lazyLoadParamsFromFile((root/"models/piw24_pose180_ZG.raw").string());
            auto device=Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000");
            device.setWaitTime(10000);
            auto version=device.version();
            require(version.count("device") && version.at("device")=="25122301"
                    && version.count("icore") && version.at("icore")=="FMSHZGV3TECH-AID - 24160628", "Actual device/icore identity differs");
            auto session=Session::Create<zg330::ZG330Backend,HostBackend>(graph.view(),{device,HostDevice::Default()});
            session.enableTimeProfile(false);
            session.apply();
            const auto final_count=validate_fusion(session,graph,output);
            uint64_t npu_calls=0, host_compute_calls=0;
            session.setPostCallBack([&](const Session&,const xir::Operation& op,const Backend& backend,std::vector<Tensor>&) {
                if (backend.is<zg330::ZG330Backend>()) ++npu_calls;
                else if (!op.is<xir::Input>() && !op.is<xir::Output>()) ++host_compute_calls;
            });
            for (auto& c : cases) c.tensor=Tensor(in[0]).mallocOn(HostDevice::MemRegion());
            text_file(output/"initialized.json","{\"initialization_ms\":"+std::to_string(elapsed(initializing))+"}\n");
            std::ofstream actual(output/"actual.bin",std::ios::binary);
            std::ofstream rows(output/"frames.jsonl"); rows << std::setprecision(17);
            const auto begin=Clock::now();
            // 首窗首次原值已离线核验，不重跑；本次verify只补另外两份输入。
            while ((stage=="verify" && completed<2) || (stage=="stress" && elapsed(begin)<1800000.0)) {
                const uint32_t index=uint32_t((completed+(stage=="verify"?1:0))%cases.size());
                auto& c=cases[index];
                auto start=Clock::now();
                c.tensor.write(0,reinterpret_cast<char*>(c.input.data()),c.input.size()*sizeof(float));
                device.reset(1);
                require(device.cast<ZG330Device>().layerCount()==0,"Status-only frame clear did not reach zero");
                npu_calls=0; host_compute_calls=0;
                const auto forward_begin=Clock::now();
                auto outputs=session.forward({c.tensor});
                const double forward_ms=elapsed(forward_begin);
                require(outputs.size()==2,"Runtime output count differs");
                for (const auto& t : outputs) require(t.waitForReady(std::chrono::milliseconds(10000)),"Native final output wait failed");
                const auto count=device.cast<ZG330Device>().layerCount();
                require(count==final_count,"Runtime final completion count differs");
                require(npu_calls>0 && host_compute_calls==0,"Unexpected actual Host computation");
                auto scores=dump(outputs[0],180,output/"failed-scores-partial.bin");
                auto poses=dump(outputs[1],7560,output/"failed-poses-partial.bin");
                const double process_ms=elapsed(start);
                // 每次新forward的全部首次输出先完整保存，后作比较，不用晚值修补。
                const uint32_t values=7740;
                actual.write(reinterpret_cast<const char*>(&completed),sizeof(completed));
                actual.write(reinterpret_cast<const char*>(&index),sizeof(index));
                actual.write(reinterpret_cast<const char*>(&values),sizeof(values));
                actual.write(scores.data(),scores.size()); actual.write(poses.data(),poses.size());
                require(bool(actual),"Full actual output archive write failed");
                ++saved;
                bool finite=true,selected_identity=true;
                double max_score=0,max_joint_mm=0,max_checked_joint_mm=0;
                size_t best_index=0;
                float best_score=-std::numeric_limits<float>::infinity();
                for (size_t i=0; i<180; ++i) {
                    float value; std::memcpy(&value,scores.data()+i*4,4);
                    finite=finite && std::isfinite(value);
                    max_score=std::max(max_score,std::abs(double(value)-c.scores[i]));
                    selected_identity=selected_identity && ((value>0.2f)==(c.scores[i]>0.2f));
                    if (value>best_score) {best_score=value;best_index=i;}
                }
                for (size_t j=0; j<180*14; ++j) {
                    double square=0;
                    for (size_t k=0;k<3;++k) {
                        float value;const auto i=j*3+k; std::memcpy(&value,poses.data()+i*4,4);
                        finite=finite && std::isfinite(value);
                        double delta=double(value)-c.poses[i];square+=delta*delta;
                    }
                    max_joint_mm=std::max(max_joint_mm,1000*std::sqrt(square));
                    if (c.scores[j/14]>0.2f) max_checked_joint_mm=std::max(max_checked_joint_mm,1000*std::sqrt(square));
                }
                const bool exact=scores==std::string(reinterpret_cast<const char*>(c.scores.data()),c.scores.size()*4)
                    && poses==std::string(reinterpret_cast<const char*>(c.poses.data()),c.poses.size()*4);
                const bool best_identity=best_index==size_t(std::max_element(c.scores.begin(),c.scores.end())-c.scores.begin());
                const bool accepted=finite && selected_identity && best_identity && max_score<=0.001 && max_checked_joint_mm<=3.0;
                rows << "{\"invocation\":" << completed << ",\"case_index\":" << index
                     << ",\"finite\":" << (finite?"true":"false") << ",\"instruction_reference_bitwise\":" << (exact?"true":"false")
                     << ",\"max_score_delta\":" << max_score << ",\"max_joint_delta_mm\":" << max_joint_mm
                     << ",\"max_checked_joint_delta_mm\":" << max_checked_joint_mm
                     << ",\"selected_identity\":" << (selected_identity?"true":"false") << ",\"best_identity\":" << (best_identity?"true":"false")
                     << ",\"approved_gate_accepted\":" << (accepted?"true":"false")
                     << ",\"process_ms\":" << process_ms << ",\"forward_ms\":" << forward_ms
                     << ",\"completed_layers\":" << count << ",\"npu_callbacks\":" << npu_calls << ",\"host_compute_callbacks\":0}\n";
                if (!finite || (stage=="verify" && !accepted)) {actual.flush();rows.flush();}
                require(finite,"Nonfinite model output; preserve and stop without retry");
                // 用户随后明确允许忽略数值误差直接压测；误差及候选变化仍完整记录。
                if (stage=="verify") require(accepted,"Approved 180-query instruction-consistency gate failed; stop, preserve first values, no retry");
                ++completed;
                if (completed%16==0 || stage=="verify") {
                    rows.flush();
                    text_file(output/"progress.json","{\"completed\":"+std::to_string(completed)+",\"elapsed_ms\":"+std::to_string(elapsed(begin))+"}\n");
                }
            }
            actual.flush(); rows.flush();
            require(bool(actual) && bool(rows),"Final output save failed");
            text_file(output/"inference-summary.json","{\"passed\":true,\"completed\":"+std::to_string(completed)+
                      ",\"saved\":"+std::to_string(saved)+",\"elapsed_ms\":"+std::to_string(elapsed(begin))+
                      ",\"unique_sources\":3,\"topk\":0,\"host_compute\":0,\"unthrottled\":true,\"numeric_errors_ignored\":"+
                      std::string(stage=="stress"?"true":"false")+"}\n");
            session.setPostCallBack(Session::CallBackFunc{});
        }
        text_file(output/"summary.json","{\"passed\":true,\"completed\":"+std::to_string(completed)+",\"resources_destroyed\":true}\n");
        std::cout << "Completed " << completed << " new inference calls\n";
        return 0;
    } catch (const std::exception& e) {
        if (!output.empty() && fs::is_directory(output)) {
            text_file(output/"failure.json","{\"error\":"+quoted(e.what())+",\"completed\":"+std::to_string(completed)+
                      ",\"saved\":"+std::to_string(saved)+",\"automatic_retry\":false}\n");
        }
        std::cerr << e.what() << '\n';
        return 1;
    }
}
