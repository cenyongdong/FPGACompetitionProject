// Native HDMI raster; model outputs remain unmodified owning values.
#pragma once
#include <cstddef>
#include "skeleton_render.hpp"
#include "hdmi_format.hpp"
#include <array>
#include <cstdint>
#include <vector>

namespace pose::hdmi {
    struct Rendered {
        std::vector<uint8_t> rgb565;
        unsigned top_index = 0, clipped_joints = 0;
        float score = 0;
        std::array<float, 42> selected_raw{};
        std::array<std::array<double, 2>, 14> projected{};
        double render_ms = 0;
    };

    // Ordinary owning memory only; no model-value processing or SDK access.
    struct PreparedBackground { std::vector<uint8_t> rgb565; };
    PreparedBackground prepare_background();
    Rendered render(PreparedBackground&& prepared,
                    const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id,
                    pose_v1::render::Status status = pose_v1::render::Status::Result);

    Rendered render(const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id,
                    pose_v1::render::Status status = pose_v1::render::Status::Result);
}
