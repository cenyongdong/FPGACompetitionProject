#include "preprocess.hpp"
#include <chrono>
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--self-test") {
            pose_v1::RawCsi raw{};
            raw.fill({1.0,0.0});
            auto output = pose_v1::preprocess(raw);
            for (std::size_t i=0; i<output.size(); ++i)
                if (output[i] != (i%60<30 ? 1.0f : 0.0f))
                    throw std::runtime_error("Constant CSI check failed");
            raw[0] = {std::numeric_limits<double>::quiet_NaN(), 0};
            bool rejected = false;
            try { pose_v1::preprocess(raw); } catch (const std::runtime_error&) { rejected = true; }
            if (!rejected) throw std::runtime_error("NaN not rejected");
            std::cout << "SELF_TEST_PASS: constant CSI/layout and non-finite rejection\n";
            return 0;
        }
        if (argc != 3) {
            std::cerr << "Usage: pose_preprocess_check input.csi output.f32 | --self-test\n";
            return 2;
        }
        auto window = pose_v1::read_window(argv[1]);
        const auto start = std::chrono::steady_clock::now();
        auto output = pose_v1::preprocess(window.csi);
        const auto end = std::chrono::steady_clock::now();
        pose_v1::write_tokens(argv[2], output);
        std::cout << "{\"frame_id\":" << window.frame_id << ",\"shape\":[1,180,60],\"preprocess_ms\":"
                  << std::chrono::duration<double,std::milli>(end-start).count() << "}\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << e.what() << '\n';
        return 1;
    }
}
