#include "hdmi_renderer.hpp"
#include "raster565.hpp"
#include <algorithm>
#include <chrono>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <utility>

namespace pose::hdmi {
    namespace {
        using namespace detail;
        constexpr double center_x = 780, center_y = 535;
        // Preserve the former 720p raster's physical size after its 3:2 upscale.
        // The viewport expands, but skeletons and their joint labels do not.
        constexpr double raster_scale = 1.5;

        std::array<double, 2> project(double a, double b, double c) {
            const auto old = pose_v1::render::project(a, b, c);
            return {center_x + (old[0] - 460) * raster_scale,
                    center_y + (old[1] - 355) * raster_scale};
        }

        const std::vector<uint8_t>& background() {
            static const std::vector<uint8_t> pixels = [] {
                std::vector<uint8_t> image(frame_bytes);
                for (int y = 0; y < height; ++y) {
                    const unsigned v = 16 + y * 10 / height;
                    rect(image, 0, y, width, y + 1, color(v, v + 5, v + 14));
                }
                rect(image, panel, 0, width, height, color(25, 35, 49));
                rect(image, 0, 0, panel, 96, color(20, 30, 44));
                text(image, 42, 30, "WIFI 3D POSE", 6, color(229, 237, 247));
                text(image, 1590, 34, "PS/NPU", 4, color(93, 207, 235));
                const auto label = color(167, 184, 204);
                text(image, 1592, 150, "FRAME", 3, label);
                text(image, 1592, 270, "TOP SLOT", 3, label);
                text(image, 1592, 414, "SCORE", 3, label);
                text(image, 1592, 558, "STATUS", 3, label);
                text(image, 1592, 720, "14 JOINTS", 3, label);
                text(image, 1592, 798, "MODEL UNITS", 2.5, label);
                text(image, 1592, 846, "NO CALIBRATION", 2.5, label);
                text(image, 42, 1044, "HIGHEST SCORE / NO TRACKING / FIXED VIEW", 3,
                     color(143, 163, 186));

                const auto grid = color(48, 63, 78);
                for (double v = 0.25; v <= 3.75; v += 0.5) {
                    auto a = project(v, 0.25, 4.2), b = project(v, 3.75, 4.2);
                    line(image, a[0], a[1], b[0], b[1], grid);
                    a = project(0.25, v, 4.2); b = project(3.75, v, 4.2);
                    line(image, a[0], a[1], b[0], b[1], grid);
                }
                const auto origin = project(0.5, 0.5, 4.2);
                const std::array<std::array<double, 3>, 3> ends{{
                    {{1.1, 0.5, 4.2}}, {{0.5, 1.1, 4.2}}, {{0.5, 0.5, 3.6}}
                }};
                const std::array<uint16_t, 3> colors{{
                    color(222, 121, 112), color(110, 199, 142), color(104, 168, 237)
                }};
                for (size_t i = 0; i < ends.size(); ++i) {
                    const auto p = project(ends[i][0], ends[i][1], ends[i][2]);
                    line(image, origin[0], origin[1], p[0], p[1], colors[i], 4.5);
                    if (!code(p[0], p[1]))
                        text(image, p[0] + 6, p[1] - 21,
                             i == 2 ? "-C2" : i == 0 ? "C0" : "C1", 3, colors[i]);
                }
                return image;
            }();
            return pixels;
        }
    }

    static Rendered render_impl(PreparedBackground* prepared,
                    const float* scores, const float* poses, std::size_t candidates,
                    uint64_t id, pose_v1::render::Status status) {
        const auto begin = std::chrono::steady_clock::now();
        if (!scores || !poses || (candidates != 100 && candidates != 180))
            throw std::runtime_error("Unsupported candidate raster input");
        for (std::size_t i=0;i<candidates;++i)
            if (!std::isfinite(scores[i])) throw std::runtime_error("Non-finite candidate score");
        for (std::size_t i=0;i<candidates*42;++i)
            if (!std::isfinite(poses[i])) throw std::runtime_error("Non-finite candidate pose");
        using pose_v1::render::Status;
        if (status != Status::Result && status != Status::NoInput && status != Status::Stopped)
            throw std::runtime_error("Unknown result status");

        if (prepared && prepared->rgb565.size() != frameBytes)
            throw std::runtime_error("Prepared HDMI background byte count differs");
        Rendered result;
        result.top_index = unsigned(std::max_element(scores, scores+candidates) - scores);
        result.score = scores[result.top_index];
        std::copy_n(poses + result.top_index * 42, 42, result.selected_raw.begin());
        if (prepared) result.rgb565 = std::move(prepared->rgb565);
        else result.rgb565 = background(); // Existing one-call API keeps its timing scope.
        const auto white = color(236, 241, 247);
        // 20 decimal uint64 digits fit within the narrowed 352px information panel.
        text(result.rgb565, 1592, 194, std::to_string(id), 2, white);
        text(result.rgb565, 1592, 318, std::to_string(result.top_index), 4.5, white);
        std::ostringstream score;
        score << std::fixed << std::setprecision(4) << result.score;
        std::string shown = score.str();
        if (shown.size() > 15) shown = "OUT OF RANGE";
        text(result.rgb565, 1592, 462, shown, 3, color(255, 122, 112));
        text(result.rgb565, 1592, 606,
             status == Status::Result ? "RESULT" : status == Status::NoInput ? "NO INPUT" : "STOPPED",
             3, color(130, 221, 164));

        for (size_t i = 0; i < result.projected.size(); ++i) {
            result.projected[i] = project(result.selected_raw[i * 3],
                                          result.selected_raw[i * 3 + 1],
                                          result.selected_raw[i * 3 + 2]);
            if (code(result.projected[i][0], result.projected[i][1])) ++result.clipped_joints;
        }
        if (status == Status::Result) {
            for (const auto bone : pose_v1::render::bones) {
                const auto a = result.projected[bone[0]], b = result.projected[bone[1]];
                line(result.rgb565, a[0], a[1], b[0], b[1], color(255, 91, 94), 4.5);
            }
            for (size_t i = 0; i < result.projected.size(); ++i) {
                const auto p = result.projected[i];
                if (code(p[0], p[1])) continue;
                const int x = int(std::lround(p[0])), y = int(std::lround(p[1]));
                for (int dy = -6; dy <= 6; ++dy)
                    for (int dx = -6; dx <= 6; ++dx)
                        if (dx * dx + dy * dy <= 36)
                            pixel(result.rgb565, x + dx, y + dy, color(255, 204, 185));
                // Old 1px glyph scale and offsets multiplied only by the existing 1.5 upscale.
                text(result.rgb565, x + 10.5, y - 15, std::to_string(i), 1.5,
                     color(236, 231, 224));
            }
        }
        result.render_ms = std::chrono::duration<double, std::milli>(
            std::chrono::steady_clock::now() - begin).count();
        return result;
    }
    PreparedBackground prepare_background() {
        return PreparedBackground{background()};
    }
    void prepare_background(PreparedBackground& reusable) {
        reusable.rgb565.assign(background().begin(),background().end());
    }
    Rendered render(PreparedBackground&& prepared, const float* scores,
                    const float* poses, std::size_t candidates, uint64_t id,
                    pose_v1::render::Status status) {
        return render_impl(&prepared,scores,poses,candidates,id,status);
    }

    Rendered render(PreparedBackground&& prepared,
                    const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id, pose_v1::render::Status status) {
        return render_impl(&prepared, scores.data(), poses.data(), scores.size(), id, status);
    }

    Rendered render(const std::array<float, 100>& scores,
                    const std::array<float, 4200>& poses,
                    uint64_t id, pose_v1::render::Status status) {
        return render_impl(nullptr, scores.data(), poses.data(), scores.size(), id, status);
    }

}
