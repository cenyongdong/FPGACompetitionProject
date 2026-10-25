// SDK-independent tests of unchanged 100-slot output and new 180-slot display.
#include "hdmi_renderer.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <iostream>
#include <stdexcept>
#include <utility>

namespace {
namespace hdmi = pose::hdmi;
using Status = pose_v1::render::Status;
void expect(bool yes, const char* message) {
    if (!yes) throw std::runtime_error(message);
}

template<std::size_t Candidates>
void fill_model(std::array<float, Candidates>& scores, std::array<float, Candidates * 42>& poses,
                std::size_t selected) {
    scores.fill(0.125f);
    scores[selected] = 0.9375f;
    for (std::size_t slot = 0; slot < Candidates; ++slot)
        for (std::size_t joint = 0; joint < 14; ++joint) {
            const auto offset = slot * 42 + joint * 3;
            poses[offset] = 1.25f + float(joint % 4) * 0.125f + float(slot) / 1024.0f;
            poses[offset + 1] = 1.5f + float(joint % 3) * 0.1875f;
            poses[offset + 2] = 2.75f + float(joint) * 0.0625f;
        }
}

void compare_display_values(const hdmi::Rendered& old, const hdmi::Rendered& current) {
    expect(old.rgb565 == current.rgb565, "100-slot compatibility changed RGB565 pixels");
    expect(old.top_index == current.top_index && old.score == current.score,
           "100-slot compatibility changed the highest score selection");
    expect(old.selected_raw == current.selected_raw && old.projected == current.projected
        && old.clipped_joints == current.clipped_joints,
        "100-slot compatibility changed selected model coordinates or projection");
}

void old_100_wrapper_matches_pointer_100() {
    std::array<float, 100> scores;
    std::array<float, 4200> poses;
    fill_model(scores, poses, 73);
    for (auto status : {Status::Result, Status::NoInput, Status::Stopped}) {
        const auto original_scores = scores;
        const auto original_poses = poses;
        const auto old = hdmi::render(scores, poses, 12345678901234567890ull, status);
        auto background = hdmi::prepare_background();
        const auto current = hdmi::render(std::move(background), scores.data(), poses.data(),
                                          scores.size(), 12345678901234567890ull, status);
        compare_display_values(old, current);
        expect(scores == original_scores && poses == original_poses,
               "Rendering modified model output values");
    }
}

void new_180_selects_last_candidate_and_reuses_canvas() {
    std::array<float, 180> scores;
    std::array<float, 7560> poses;
    fill_model(scores, poses, 179);
    const auto original_scores = scores;
    const auto original_poses = poses;
    auto background = hdmi::prepare_background();
    auto* const canvas = background.rgb565.data();
    const auto capacity = background.rgb565.capacity();
    expect(background.rgb565.size() == hdmi::frameBytes, "Prepared canvas dimensions differ");
    for (std::uint64_t frame = 1; frame <= 3; ++frame) {
        auto rendered = hdmi::render(std::move(background), scores.data(), poses.data(), scores.size(), frame);
        expect(rendered.rgb565.data() == canvas && rendered.rgb565.capacity() == capacity,
               "Rendering allocated another CPU frame instead of moving reusable storage");
        expect(rendered.top_index == 179 && rendered.score == scores[179],
               "180-slot renderer ignored the highest candidate at index 179");
        expect(!std::memcmp(rendered.selected_raw.data(), poses.data() + 179 * 42, 168),
               "180-slot renderer selected another candidate's pose bytes");
        for (std::size_t joint = 0; joint < 14; ++joint) {
            const auto offset = 179 * 42 + joint * 3;
            const auto original = pose_v1::render::project(poses[offset], poses[offset + 1], poses[offset + 2]);
            const std::array<double, 2> expected{{780 + (original[0] - 460) * 1.5,
                                                  535 + (original[1] - 355) * 1.5}};
            expect(rendered.projected[joint] == expected, "180-slot rendering changed the established projection");
        }
        // A fresh canvas for the same frame detects stale skeletons/labels when
        // the recycled buffer is refilled from the immutable prepared base.
        auto fresh = hdmi::prepare_background();
        auto reference = hdmi::render(std::move(fresh), scores.data(), poses.data(), scores.size(), frame);
        expect(rendered.rgb565 == reference.rgb565, "Reused CPU canvas retained a previous frame's pixels");
        background.rgb565 = std::move(rendered.rgb565);
        hdmi::prepare_background(background);
        expect(background.rgb565.data() == canvas && background.rgb565.capacity() == capacity,
               "Replenishing the reusable background allocated another frame buffer");
    }
    expect(scores == original_scores && poses == original_poses, "180-slot rendering modified model outputs");
}
} // namespace

int main() {
    try {
        old_100_wrapper_matches_pointer_100();
        new_180_selects_last_candidate_and_reuses_canvas();
        std::cout << "pose180 renderer compatibility/reuse contracts passed\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "pose180 renderer test failed: " << e.what() << '\n';
        return 1;
    }
}
