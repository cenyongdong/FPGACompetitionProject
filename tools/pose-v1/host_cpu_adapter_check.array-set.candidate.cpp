// Standalone CPU diagnostics only. No Session, Device::Open or ZG backend.
#include "host_cpu_adapter.hpp"
#include <icraft-xir/ops/ops.h>
#include <icraft-xrt/dev/host_device.h>
#include <algorithm>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <sstream>

namespace fs = std::filesystem;
namespace xir = icraft::xir;
namespace xrt = icraft::xrt;
namespace candidate = pose_v1::cpu_candidate;
static void require(bool yes, const std::string& message) {
    if (!yes) throw std::runtime_error(message);
}
static std::vector<char> read(const fs::path& path) {
    std::ifstream in(path, std::ios::binary | std::ios::ate);
    require(bool(in), "Missing fixture: " + path.string());
    const auto size = in.tellg();
    require(size >= 0 && size <= 1024*1024, "Fixture file has invalid size");
    std::vector<char> data(static_cast<size_t>(size));
    in.seekg(0); in.read(data.data(), static_cast<std::streamsize>(data.size()));
    require(bool(in), "Cannot read fixture"); return data;
}
static void write(const fs::path& path, const std::vector<char>& bytes) {
    std::ofstream out(path, std::ios::binary);
    out.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
    require(bool(out), "Cannot write evidence: " + path.string());
}
struct Case { std::string name, expected, mutation; int64_t id; bool buffers; };
static std::vector<Case> cases(const fs::path& path) {
    std::ifstream in(path); std::string line;
    require(bool(in) && bool(std::getline(in,line)) &&
        line == "case_id\top_id\texpected\tmutation\tbuffers", "Invalid LF cases.tsv header");
    std::vector<Case> list;
    while (std::getline(in,line)) {
        std::istringstream row(line); std::vector<std::string> fields;
        for (std::string field; std::getline(row,field,'\t');) fields.push_back(field);
        require(fields.size() == 5 && fields[0].find_first_not_of("abcdefghijklmnopqrstuvwxyz0123456789_-") == std::string::npos,
                "Unsafe/malformed case record");
        require(fields[4] == "0" || fields[4] == "1", "Invalid buffer flag");
        list.push_back({fields[0],fields[2],fields[3],std::stoll(fields[1]),fields[4] == "1"});
    }
    require(!list.empty(), "Empty case list"); return list;
}
static xir::TensorType type_with(const xir::TensorType& old,
                                xir::Array<xir::MergedAxisDistr> distributions) {
    return xir::TensorType(old->element_dtype, old->shape, old->layout, distributions);
}
static void mutate(xir::Operation op, const std::string& mutation) {
    if (mutation == "none" || mutation == "byte_mismatch" || mutation == "wrong_output" ||
        mutation == "output_count" || mutation == "missing_runtime" || mutation == "extra_runtime") return;
    if (mutation == "axis") {
        if (op.is<xir::TopK>()) op.cast<xir::TopK>().get_mutable()->axis = 99;
        else op.cast<xir::GatherElements>().get_mutable()->axis = 99;
    } else if (mutation == "sorted") op.cast<xir::TopK>().get_mutable()->sorted = false;
    else if (mutation == "reduction") op.cast<xir::ScatterND>().get_mutable()->reduction = xir::Reduction::ADD;
    else {
        auto old = op->inputs[0]; auto type = old.tensorType();
        if (mutation == "dtype")
            type = xir::TensorType(xir::FloatType::FP16(),type->shape,type->layout,type->merged_distrs);
        else if (mutation == "shape") {
            xir::Array<int64_t> dims(std::vector<int64_t>(type->shape.begin(),type->shape.end()));
            dims.set(-1, dims[-1] - 1);
            type = xir::TensorType(type->element_dtype,dims,type->layout,type->merged_distrs);
        } else if (mutation == "layout") {
            std::string permuted(type->shape.size(),'*');
            if (type->shape.size() > 1) permuted[0] = 'C';
            type = xir::TensorType(type->element_dtype,type->shape,xir::Layout(permuted),type->merged_distrs);
        } else if (mutation == "mask_gap" || mutation == "mask_length" || mutation == "mask_axis") {
            require(type->merged_distrs.size() == 1, "Mask mutation requires one frozen distribution");
            const auto distribution = type->merged_distrs[0];
            auto mask_size = static_cast<int64_t>(distribution->valid_mask.size());
            auto bad = xir::MergedAxisDistr(distribution->merged_axis,
                mutation == "mask_length" ? mask_size-1 : mask_size, true);
            bad.setUValue(xir::DistrUnvalidValue::ZERO);
            if (mutation == "mask_gap") bad.setUnvalid(0,1);
            if (mutation == "mask_axis") bad.setMergedAxis({99});
            type = type_with(type,{bad});
        } else throw std::runtime_error("Unknown mutation: " + mutation);
        op.setInput(0,xir::Value(old->name,type).setId(old->v_id));
    }
}
static std::vector<xrt::Tensor> load_inputs(xir::Operation op, const fs::path& dir) {
    std::vector<xrt::Tensor> runtime;
    for (size_t i = 0; i < op->inputs.size(); ++i) {
        auto value = op->inputs[i]; auto type = value.tensorType();
        auto bytes = read(dir/("input"+std::to_string(i)+".f32"));
        require(bytes.size() == type.bytes(), "Fixture/declaration byte count mismatch");
        if (value.isParams()) {
            std::shared_ptr<char[]> buffer(new char[bytes.size()]);
            std::memcpy(buffer.get(),bytes.data(),bytes.size());
            // Substitute synthetic parameters in this fresh in-memory graph only.
            xir::Params params(buffer,value->name,type);
            params.setId(value->v_id); op.setInput(static_cast<int64_t>(i),params);
        } else {
            auto tensor = xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
            tensor.write(0,bytes.data(),bytes.size()); runtime.push_back(tensor);
        }
    }
    return runtime;
}
static std::vector<char> tensor_bytes(const xrt::Tensor& tensor) {
    require(tensor.isOn(xrt::HostDevice::MemRegion()) && tensor.hasData(), "Non-Host result");
    std::vector<char> bytes(static_cast<size_t>(tensor.dtype().bytes()));
    tensor.read(bytes.data(),0,bytes.size()); return bytes;
}
static void registration(std::ostream& log, xrt::HostBackend backend, xir::Network graph,
                         const char* phase) {
    for (int64_t id : {188,192,437,442,582,649}) {
        auto op = graph.getOpById(id);
        log << "{\"phase\":" << std::quoted(phase) << ",\"op_id\":" << id
            << ",\"supported\":" << (backend.isOpSupported(op)?"true":"false")
            << ",\"init\":" << (backend.getInitFunc(op)?"true":"false")
            << ",\"forward\":" << (backend.getForwardFunc(op)?"true":"false") << "}\n";
    }
    log.flush();
}
int main(int argc, char** argv) {
    try {
        require(argc == 7 && std::string(argv[1]) == "--graph" &&
                std::string(argv[3]) == "--fixtures" && std::string(argv[5]) == "--output",
                "Usage: pose_cpu_adapter_check --graph JSON --fixtures DIR --output NEW_DIR");
        const fs::path output(argv[6]), fixture(argv[4]);
        require(!fs::exists(output), "Preserve existing output; refuse overwrite");
        require(fs::create_directories(output), "Cannot create evidence directory");
        std::ofstream log(output/"cases.jsonl"), registry(output/"registry.jsonl");
        require(bool(log) && bool(registry), "Cannot create logs");
        uint16_t little = 1;
        require(sizeof(float) == 4 && *reinterpret_cast<char*>(&little) == 1,"Requires little-endian float32");
        auto baseline = xir::Network::CreateFromJsonFile(argv[2]);
        require(baseline->icraft_version == "v3.39.0" && baseline->icraft_xir_version == "3.39.0.0" &&
                !baseline->swap_mode, "Model SDK/swap baseline differs");
        auto backend = xrt::HostBackend::Init();
        const auto bk = xrt::HostBackend::NodeType::type_key;
        const auto mm = xir::Matmul::NodeType::type_key;
        require(!xrt::BackendOpRegistry::GetInitFunc(bk,mm) &&
                !xrt::BackendOpRegistry::GetForwardFunc(bk,mm), "Matmul registration baseline changed");
        registration(registry,backend,baseline,"before");
        candidate::register_missing(baseline,backend);
        registration(registry,backend,baseline,"after");
        require(!xrt::BackendOpRegistry::GetInitFunc(bk,mm) &&
                !xrt::BackendOpRegistry::GetForwardFunc(bk,mm), "Candidate unexpectedly registered Matmul");
        size_t passed = 0;
        const auto list = cases(fixture/"cases.tsv");
        for (const auto& test : list) {
            // Fresh parse ensures test mutations cannot leak into another case.
            auto graph = xir::Network::CreateFromJsonFile(argv[2]);
            auto op = graph.getOpById(test.id);
            auto runtime = load_inputs(op,fixture/test.name);
            mutate(op,test.mutation);
            if (test.mutation == "byte_mismatch") {
                auto type = runtime[0].dtype();
                xir::Array<int64_t> dims(std::vector<int64_t>(type->shape.begin(),type->shape.end()));
                dims.set(-1, dims[-1] - 1);
                runtime[0] = xrt::Tensor(xir::TensorType(type->element_dtype,dims,type->layout))
                    .mallocOn(xrt::HostDevice::MemRegion());
            }
            if (test.mutation == "missing_runtime") runtime.clear();
            if (test.mutation == "extra_runtime") runtime.push_back(runtime[0]);
            std::vector<xrt::Tensor> buffers;
            if (test.buffers) for (const auto& value : op->outputs) {
                auto tensor = xrt::Tensor(value.tensorType()).mallocOn(xrt::HostDevice::MemRegion());
                std::memset(tensor.data().cptr(),0,static_cast<size_t>(tensor.dtype().bytes())); buffers.push_back(tensor);
            }
            if (test.mutation == "wrong_output") {
                auto type = buffers[0].dtype();
                xir::Array<int64_t> dims(std::vector<int64_t>(type->shape.begin(),type->shape.end()));
                dims.set(-1, dims[-1] - 1);
                buffers[0] = xrt::Tensor(xir::TensorType(type->element_dtype,dims,type->layout))
                    .mallocOn(xrt::HostDevice::MemRegion());
            }
            if (test.mutation == "output_count") buffers.pop_back();
            auto isolated = xrt::HostBackend::Init();
            std::string rejected;
            std::vector<xrt::Tensor> results;
            try {
                if (test.id == 442) {
                    // Existing Gather may require its original backend state.
                    // Initialize just this CPU op on HostDevice, never a Session.
                    isolated.init(graph.view(std::vector<int64_t>{test.id}),xrt::HostDevice::Default());
                    results = isolated.forwardOp(op,runtime,buffers);
                } else {
                    // Exercise the actual registered ABI without initializing
                    // the SDK engine on deliberately malformed negative cases.
                    isolated.getInitFunc(op).value()(op,isolated);
                    results = isolated.getForwardFunc(op).value()(op,runtime,buffers,isolated);
                }
            } catch (const candidate::Rejection& error) {
                rejected = error.code();
            }
            if (test.expected == "PASS") {
                require(rejected.empty(), "Unexpected rejection " + rejected + " in " + test.name);
                require(results.size() == op->outputs.size(), "Result count mismatch");
                const auto case_out = output/test.name; fs::create_directory(case_out);
                for (size_t i = 0; i < results.size(); ++i) {
                    require(results[i].dtype() == op->outputs[i].tensorType(),"Output dtype changed");
                    auto bytes = tensor_bytes(results[i]);
                    write(case_out/("output"+std::to_string(i)+".f32"),bytes);
                    require(bytes == read(fixture/test.name/("expected"+std::to_string(i)+".f32")),
                            "Bitwise reference mismatch in " + test.name);
                    if (test.buffers) require(tensor_bytes(buffers[i]) == bytes,
                                             "Supplied output buffer was not filled");
                }
            } else require(rejected == test.expected,
                    "Expected rejection " + test.expected + ", got " + rejected + " in " + test.name);
            log << "{\"case_id\":" << std::quoted(test.name) << ",\"op_id\":" << test.id
                << ",\"expected\":" << std::quoted(test.expected) << ",\"rejection\":" << std::quoted(rejected)
                << ",\"passed\":true}\n"; log.flush(); ++passed;
            if (test.id == 442) isolated.deinit();
        }
        std::ofstream summary(output/"summary.json");
        summary << "{\"status\":\"cpu_candidate_tests_passed\",\"case_count\":" << passed
                << ",\"device_opened\":false,\"full_model_executed\":false,\"mixed_verified\":false}\n";
        require(bool(summary), "Cannot save summary");
        std::cout << "CPU-only candidate gate completed, " << passed << " cases; mixed remains unverified.\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "STOP (no retry): " << error.what() << '\n'; return 1;
    }
}
