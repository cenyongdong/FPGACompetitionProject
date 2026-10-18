// 有界HDMI接入入口；冻结共享Engine与SDK无关渲染经最小适配协作。
#include "resident_support.hpp"
#include "hdmi_output.hpp"
#include "hdmi_canvas.hpp"
#include "skeleton_render.hpp"
#include <thread>

int main(int argc, char** argv) {
    fs::path output;
    std::unique_ptr<app::Engine> engine;
    std::unique_ptr<pose::hdmi::Output> display;
    try {
        need(argc == 4 && std::string(argv[3]) == "--allow-device-init", "Expected package, fresh output and explicit device flag");
        const fs::path package(argv[1]);
        output = argv[2];
        need(!fs::exists(output) && fs::create_directory(output), "Fresh HDMI demo directory required");
        need(fs::create_directory(output / "engine"), "Fresh Engine evidence directory required");
        const auto cases = load_cases(package);
        fc::configure(3);
        pose_v1::timing_sdk::configure(false);
        pose::failure_evidence::configure(output / "failed-host-inputs");
        pose::source_diagnostic::configure(output / "failed-host-inputs/source-readback");
        pose::stage_observation::configure(output / "copy-observations", {}, 3);
        pose::producer_count::configure(output / "producer-counts");
        pose::tensor_identity::configure(output / "tensor-identities", 3);
        app::Config config;
        config.graph = package / "models/piw24_shared_ZG.json";
        config.raw = package / "models/piw24_shared_ZG.raw";
        config.evidence = output / "engine";
        config.allow_device_init = true;
        config.minimal_log = true;
        config.diagnostic_frames = 0;
        config.timing_frames = 3;
        // 在Session完成分配后，由Engine主线程显式传递同一设备引用。
        // 没有第二次Device::Open或独立进程的UDMA分配器。
        config.on_device_ready = [&](const icraft::xrt::Device& device) {
            display = std::make_unique<pose::hdmi::Output>(device, output / "hdmi.jsonl");
            display->verifyMemory();
        };
        engine = std::make_unique<app::Engine>(config);
        need(bool(display), "HDMI device-owner hook not invoked");
        std::ofstream frames(output / "frames.jsonl");
        frames << std::setprecision(17);
        size_t completed = 0;
        for (const auto& c : cases) {
            const auto actual = engine->process_window_checked(c.window, c.name, c.input);
            const auto folder = output / ("frame-" + std::to_string(actual.invocation));
            need(fs::create_directory(folder), "Fresh frame directory required");
            save_array(folder / "input.f32", actual.input);
            save_array(folder / "scores.f32", actual.scores);
            save_array(folder / "poses.f32", actual.poses);
            const auto gate = pose::shared_output_gate::compare(actual.scores, c.scores, actual.poses, c.poses, 3.0, 0.2f);
            frames << "{\"event\":\"numeric\",\"case\":" << quote(c.name) << ",\"frame_id\":" << actual.frame_id
                   << ",\"invocation\":" << actual.invocation << ",\"accepted\":" << (gate.accepted ? "true" : "false")
                   << ",\"scores_bitwise_equal\":" << (gate.scores_bitwise_equal ? "true" : "false")
                   << ",\"finite\":" << (gate.finite ? "true" : "false")
                   << ",\"checked_candidates\":" << gate.checked_candidates
                   << ",\"max_checked_joint_delta_mm\":" << gate.max_checked_joint_delta_mm
                   << ",\"completed_layers\":" << actual.completed_layers << ",\"process_ms\":" << actual.process_ms << "}\n";
            frames.flush();
            need(bool(frames) && gate.accepted, "Actual saved; numeric gate failed, stop without retry");
            const auto rendered = pose_v1::render::draw(actual.scores, actual.poses, actual.frame_id);
            auto pixels = pose::hdmi::canvas(rendered.rgb);
            save_array(folder / "selected.f32", rendered.selected_raw);
            save_array(folder / "projected.f64", rendered.projected);
            std::ofstream raw(folder / "skeleton.rgb565", std::ios::binary);
            raw.write(reinterpret_cast<const char*>(pixels.data()), pixels.size()); raw.close();
            need(bool(raw), "HDMI source save failed");
            need(actual.frame_id > 0 && actual.frame_id <= UINT32_MAX, "HDMI frame ID exceeds contract");
            display->show(pixels, uint32_t(actual.frame_id));
            frames << "{\"event\":\"rendered\",\"case\":" << quote(c.name) << ",\"frame_id\":" << actual.frame_id
                   << ",\"selected_candidate\":" << rendered.top_index << ",\"clipped_joints\":" << rendered.clipped_joints
                   << ",\"bytes\":" << pixels.size() << "}\n";
            frames.flush();
            std::cout << "HDMI_SKELETON_VISIBLE case=" << c.name << " frame=" << actual.frame_id << std::endl;
            // 首次有界实屏观察：每份实际结果保持5秒，重复扫描不计新姿态。
            for (unsigned n = 0; n < 50; ++n) {
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
                display->observe();
            }
            ++completed;
        }
        display->close();
        display.reset();
        save_diagnostics(engine.get(), output);
        engine.reset();
        std::ofstream summary(output / "summary.json");
        summary << "{\"fresh_inferences\":" << completed << ",\"HDMI_frames_adopted\":" << completed
                << ",\"VPU_started\":false,\"RTSP_started\":false,\"STOP_and_release_completed\":true,\"engine_destroyed\":true,\"strict_realtime_or_longterm_verified\":false}\n";
        need(bool(summary), "Cannot save HDMI completion summary");
        std::cout << "HDMI_SHARED_THREE_PASS" << std::endl;
        return 0;
    } catch (const std::exception& error) {
        const auto original = std::string(error.what());
        // 保持原失败；显示先停止并证明排空，再销毁SDK Engine。
        display.reset();
        if (!output.empty() && fs::is_directory(output)) {
            try { save_diagnostics(engine.get(), output); } catch (...) {}
            std::ofstream failure(output / "failure.json");
            failure << "{\"error\":" << quote(original) << ",\"retry\":false}\n";
        }
        engine.reset();
        std::cerr << "HDMI_SHARED_STOP " << original << std::endl;
        return 1;
    }
}
