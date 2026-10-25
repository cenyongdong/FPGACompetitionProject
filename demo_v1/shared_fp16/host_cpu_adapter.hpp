// 推理模块：固定模型、CPU适配及公开SDK桥；保持单Engine和原计算、搬运顺序。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

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
        Rejection(std::string code, const std::string& detail) : std::runtime_error("CPU_CANDIDATE[" + code + "]: " + detail), code_(std::move(code)) {} const std::string& code() const {
            return code_;
        }

        private:
        std::string code_;
    };
    // 1. 验证固定FP32形状、轴和全有效分布，拒绝未批准规格。
    void validate_spec(const icraft::xir::Operation& op);
    // 2. 显式注册缺失CPU算子；不覆盖已有或部分注册。
    void register_missing(const icraft::xir::Network& graph, icraft::xrt::HostBackend backend);
    std::vector<icraft::xrt::Tensor> forward(const icraft::xir::Operation& op, const std::vector<icraft::xrt::Tensor> & inputs, const std::vector<icraft::xrt::Tensor> & outputs);
}

// namespace pose_v1::cpu_candidate
