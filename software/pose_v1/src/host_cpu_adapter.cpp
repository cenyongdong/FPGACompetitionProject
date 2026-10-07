#include "host_cpu_adapter.hpp"
#include <icraft-backends/hostbackend/port/common/tensor_ops.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <set>

namespace pose_v1::cpu_candidate {
namespace xir = icraft::xir;
namespace xrt = icraft::xrt;
namespace kernel = icraft::hostbackend::common;
namespace port = icraft::hostbackend::port;
namespace {
void need(bool condition, const char* code, const std::string& detail) {
    if (!condition) throw Rejection(code, detail);
}
bool shape(const xir::TensorType& type, std::initializer_list<int64_t> dims) {
    return type->shape.size() == dims.size() &&
        std::equal(type->shape.begin(), type->shape.end(), dims.begin());
}
void fp32(const xir::TensorType& type) {
    need(type->element_dtype.is<xir::FloatType>() && type->element_dtype.isFP32(),
         "dtype", "Only unquantized FP32 is approved");
}
void layout(const xir::TensorType& type) {
    need(type->layout.numAxis() == type->shape.size(), "layout", "Layout rank mismatch");
    // Current model layouts are *, *C or **C (Scatter indices: ***C),
    // with C last. No packed/split/channel permutations are supported.
    for (size_t axis = 0; axis < type->shape.size(); ++axis) {
        const char expected = axis + 1 == type->shape.size() ? 'C' : '*';
        need(type->layout.getAxisCharName(static_cast<int64_t>(axis)) == expected,
             "layout", "Only the frozen model's row-major *...C layout is approved");
    }
}
void check_type(const xir::TensorType& type) { fp32(type); layout(type); }
void check_distribution(const xir::TensorType& type) {
    for (const auto& distribution : type->merged_distrs) {
        need(distribution->uvalue == xir::DistrUnvalidValue::ZERO,
             "distribution", "Only ZERO full-valid distributions are approved");
        size_t extent = 1;
        std::set<int64_t> axes;
        for (int64_t axis : distribution->merged_axis) {
            need(axis >= 0 && static_cast<size_t>(axis) < type->shape.size() && axes.insert(axis).second,
                 "distribution", "Invalid or duplicate distribution axis");
            need(type->shape[axis] > 0 && static_cast<uint64_t>(type->shape[axis]) <=
                 std::numeric_limits<size_t>::max() / extent, "distribution", "Invalid distribution extent");
            extent *= static_cast<size_t>(type->shape[axis]);
        }
        need(!axes.empty() && distribution->valid_mask.size() == extent &&
             std::all_of(distribution->valid_mask.begin(), distribution->valid_mask.end(),
                         [](bool value) { return value; }), "distribution", "Mask is not completely valid");
    }
}

kernel::TensorDesc dense_description(const xrt::Tensor& tensor, const xir::TensorType& declared,
                                     bool check_finite = true) {
    need(tensor.hasData(), "storage", "Tensor has no allocated data");
    need(tensor.dtype() == declared, "storage", "Runtime dtype/layout differs from declaration");
    need(tensor.offset() <= tensor.chunk()->byte_size &&
         declared.bytes() <= tensor.chunk()->byte_size - tensor.offset(),
         "storage", "Declared data extends beyond the actual memory chunk");
    // This phase deliberately cannot operate on NPU/physical/zero-copy memory.
    need(tensor.isOn(xrt::HostDevice::MemRegion()) && tensor.data().ptype() == xrt::PtrType::CPTR,
         "memory", "Diagnostic candidate accepts HostDevice memory only");
    need(tensor.isReady(), "memory", "Host input is not ready; no hardware polling is permitted");
    kernel::TensorDesc desc;
    auto status = port::describeTensor(tensor.data().cptr(),
        static_cast<size_t>(tensor.dtype().bytes()), declared,
        kernel::RoundingMode::kHalfUp, &desc);
    need(status.ok(), "storage", status.message);
    check_type(declared);
    size_t elements = 1;
    for (int64_t dim : declared->shape) {
        need(dim > 0 && static_cast<uint64_t>(dim) <= std::numeric_limits<size_t>::max() / elements,
             "storage", "Invalid or overflowing shape");
        elements *= static_cast<size_t>(dim);
    }
    need(elements <= std::numeric_limits<size_t>::max() / sizeof(float) &&
         desc.data_bytes == elements * sizeof(float), "storage", "Storage byte count mismatch");
    for (const auto& distribution : desc.distributions) {
        need(distribution.invalid_value == kernel::InvalidValue::kZero,
             "distribution", "Only ZERO full-valid distributions are approved");
        size_t extent = 1;
        std::set<int64_t> axes;
        for (int64_t axis : distribution.axes) {
            need(axis >= 0 && static_cast<size_t>(axis) < desc.shape.size() && axes.insert(axis).second,
                 "distribution", "Invalid or duplicate distribution axis");
            need(static_cast<size_t>(desc.shape[axis]) <= std::numeric_limits<size_t>::max() / extent,
                 "distribution", "Distribution extent overflow");
            extent *= static_cast<size_t>(desc.shape[axis]);
        }
        need(!axes.empty() && distribution.valid_mask.size() == extent &&
             std::all_of(distribution.valid_mask.begin(), distribution.valid_mask.end(),
                         [](unsigned char value) { return value == 1; }),
             "distribution", "Distribution is not completely valid or has an invalid mask length");
    }
    // Safe only after the checks above: remove metadata in a temporary kernel
    // descriptor. Never mutate any XIR dtype, mask, graph or input data.
    desc.distributions.clear();
    const float* values = static_cast<const float*>(desc.data);
    if (check_finite) for (size_t i = 0; i < elements; ++i)
        need(std::isfinite(values[i]), "finite", "NaN/Inf input is prohibited");
    return desc;
}

std::vector<xrt::Tensor> inputs_with_params(
    const xir::Operation& op, const std::vector<xrt::Tensor>& runtime) {
    std::vector<xrt::Tensor> result;
    size_t index = 0;
    for (const auto& value : op->inputs) {
        if (value.isParams()) {
            auto params = value.cast<xir::Params>();
            need(params.hasData(), "storage", "Fixture parameter has no data; no RAW loading is allowed");
            result.emplace_back(params);
        } else {
            need(index < runtime.size(), "arity", "Missing runtime input");
            result.push_back(runtime[index++]);
        }
    }
    need(index == runtime.size(), "arity", "Unexpected runtime inputs");
    return result;
}

template<class Op> void add() {
    // Explicit main-time registration; no global constructor or plugin scan.
    xrt::BackendOpRegisterHelper<Op, xrt::HostBackend>()
        .set_init([](const Op& op, xrt::HostBackend) { validate_spec(op); })
        .set_forward([](const Op& op, const std::vector<xrt::Tensor>& inputs,
                        const std::vector<xrt::Tensor>& outputs, xrt::HostBackend) {
            return forward(op, inputs, outputs);
        });
}
} // namespace

void validate_spec(const xir::Operation& op) {
    need(op->compile_target.is<xir::HostTarget>(), "target", "Only @hostt is approved");
    for (const auto& v : op->inputs) check_type(v.tensorType());
    for (const auto& v : op->outputs) check_type(v.tensorType());
    if (op.is<xir::TopK>()) {
        auto top = op.cast<xir::TopK>();
        need(top->axis == 1 || top->axis == -1, "axis", "Unapproved TopK axis");
        need(op->inputs.size() == 2 && op->outputs.size() == 2, "arity", "TopK arity");
        const bool first = top->axis == 1 && shape(op->inputs[0].tensorType(), {1,180}) &&
            shape(op->outputs[0].tensorType(), {1,100}) && shape(op->outputs[1].tensorType(), {1,100});
        const bool second = top->axis == -1 && shape(op->inputs[0].tensorType(), {100}) &&
            shape(op->outputs[0].tensorType(), {100}) && shape(op->outputs[1].tensorType(), {100});
        need(first || second, "shape", "Unapproved TopK shape/axis combination");
        need(shape(op->inputs[1].tensorType(), {1}) && op->inputs[1].isParams() &&
             top->largest && top->sorted, "spec", "TopK requires parameter K, largest=true, sorted=true");
    } else if (op.is<xir::GatherElements>()) {
        need(op.cast<xir::GatherElements>()->axis == 1, "axis", "Unapproved GatherElements axis");
        need(op->inputs.size() == 2 && op->outputs.size() == 1, "arity", "GatherElements arity");
        need(shape(op->inputs[0].tensorType(), {1,180,42}) &&
             shape(op->inputs[1].tensorType(), {1,100,42}) &&
             shape(op->outputs[0].tensorType(), {1,100,42}) && !op->inputs[1].isParams(),
             "shape", "Unapproved GatherElements input/output shape or parameter form");
    } else if (op.is<xir::ScatterND>()) {
        need(op.cast<xir::ScatterND>()->reduction == xir::Reduction::NONE,
             "reduction", "Only ScatterND NONE is approved");
        need(op->inputs.size() == 3 && op->outputs.size() == 1, "arity", "ScatterND arity");
        need(shape(op->inputs[0].tensorType(), {100,14,3}) &&
             shape(op->inputs[1].tensorType(), {100,14,3,3}) && op->inputs[1].isParams() &&
             shape(op->inputs[2].tensorType(), {100,14,3}) &&
             shape(op->outputs[0].tensorType(), {100,14,3}),
             "shape", "Unapproved ScatterND shape or parameter form");
    } else throw Rejection("type", "Only TopK/GatherElements/ScatterND are registered");
    for (const auto& v : op->inputs) check_distribution(v.tensorType());
    for (const auto& v : op->outputs) check_distribution(v.tensorType());
}

void register_missing(const xir::Network& graph, xrt::HostBackend backend) {
    for (int64_t id : {188,192,437,582,649}) {
        auto op = graph.getOpById(id);
        validate_spec(op);
        need(!backend.isOpSupported(op) && !backend.getInitFunc(op) && !backend.getForwardFunc(op),
             "registry", "Baseline changed or partial registration exists; never override");
    }
    auto gather = graph.getOpById(442);
    need(gather.is<xir::Gather>() && backend.isOpSupported(gather) &&
         backend.getInitFunc(gather) && backend.getForwardFunc(gather),
         "registry", "Existing Gather baseline differs");
    auto gather_init = backend.getInitFunc(gather).value().target_type().hash_code();
    auto gather_forward = backend.getForwardFunc(gather).value().target_type().hash_code();
    add<xir::TopK>(); add<xir::GatherElements>(); add<xir::ScatterND>();
    need(backend.getInitFunc(gather).value().target_type().hash_code() == gather_init &&
         backend.getForwardFunc(gather).value().target_type().hash_code() == gather_forward,
         "registry", "Gather callback types changed unexpectedly");
    for (int64_t id : {188,192,437,582,649}) {
        auto op = graph.getOpById(id);
        need(backend.isOpSupported(op) && backend.getInitFunc(op) && backend.getForwardFunc(op),
             "registry", "Registration did not become visible to HostBackend");
    }
}

std::vector<xrt::Tensor> forward(const xir::Operation& op,
    const std::vector<xrt::Tensor>& runtime, const std::vector<xrt::Tensor>& user_outputs) {
    validate_spec(op);
    auto materialized = inputs_with_params(op, runtime);
    std::vector<kernel::TensorDesc> in;
    for (size_t i = 0; i < materialized.size(); ++i)
        in.push_back(dense_description(materialized[i], op->inputs[i].tensorType()));
    need(user_outputs.empty() || user_outputs.size() == op->outputs.size(),
         "output", "Wrong number of supplied output buffers");
    std::vector<xrt::Tensor> outputs;
    std::vector<kernel::TensorDesc> out;
    for (size_t i = 0; i < op->outputs.size(); ++i) {
        auto type = op->outputs[i].tensorType();
        xrt::Tensor tensor;
        if (user_outputs.empty()) tensor = xrt::Tensor(type).mallocOn(xrt::HostDevice::MemRegion());
        else {
            tensor = user_outputs[i];
            need(tensor.hasData() && tensor.dtype() == type && tensor.dtype().bytes() == type.bytes(),
                 "output", "Supplied output dtype or byte count differs");
        }
        // Host-only outputs; finite sentinel buffers in this validation phase.
        if (user_outputs.empty()) std::memset(tensor.data().cptr(), 0, static_cast<size_t>(type.bytes()));
        outputs.push_back(tensor);
        out.push_back(dense_description(outputs.back(), type, false));
    }
    kernel::Status status;
    if (op.is<xir::TopK>()) {
        const float k = *static_cast<const float*>(in[1].data);
        need(k == 100.0f, "k", "K must be finite integer 100 matching the approved outputs");
        status = kernel::topK(in[0], in[1], out[0], out[1], op.cast<xir::TopK>()->axis, true, true);
    } else if (op.is<xir::GatherElements>()) {
        status = kernel::gatherElements(in[0], in[1], out[0], 1);
    } else {
        status = kernel::scatterND(in[0], in[1], in[2], out[0], kernel::ScatterReduction::kNone);
    }
    need(status.ok(), "kernel", status.message);
    return outputs;
}
} // namespace pose_v1::cpu_candidate
