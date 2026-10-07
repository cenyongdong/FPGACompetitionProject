#pragma once
#include <icraft-backends/hostbackend/backend.h>
#include <icraft-xir/core/network.h>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

// Isolated diagnostic candidate. Not linked into pose_inference_check.
namespace pose_v1::cpu_candidate {
class Rejection : public std::runtime_error {
public:
    Rejection(std::string code, const std::string& detail)
        : std::runtime_error("CPU_CANDIDATE[" + code + "]: " + detail), code_(std::move(code)) {}
    const std::string& code() const { return code_; }
private:
    std::string code_;
};
void validate_spec(const icraft::xir::Operation& op);
void register_missing(const icraft::xir::Network& graph, icraft::xrt::HostBackend backend);
std::vector<icraft::xrt::Tensor> forward(
    const icraft::xir::Operation& op,
    const std::vector<icraft::xrt::Tensor>& inputs,
    const std::vector<icraft::xrt::Tensor>& outputs);
} // namespace pose_v1::cpu_candidate
