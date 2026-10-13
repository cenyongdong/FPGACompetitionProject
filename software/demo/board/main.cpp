// 应用入口：主线程持有Engine；按原顺序启动、消费窗口、保存现场及回收资源。

#include "demo_video.hpp"
#include "demo_results.hpp"
#include "tcp_receiver.hpp"
#include "demo_engine.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include "demo_options.hpp"

namespace {
    uint64_t now() {
        return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
    }

    void need(bool v, const char* m) {
        if (!v) throw std::runtime_error(m);
    }

}

int main(int argc, char * * argv) {
    namespace fs = std::filesystem;
    fs::path out;
    std::unique_ptr<pose::display::Process > display;
    std::unique_ptr<wifi_demo::Video > video;
    std::unique_ptr<wifi_demo::Engine > engine;
    std::unique_ptr<pose_v1::transport::Receiver > input;
    std::ofstream lifecycle;
    wifi_demo::Results results;
    std::exception_ptr failure;
    uint64_t received = 0, overwritten = 0;
    try {
        // 1. 参数解析独立于设备初始化，所有默认值和拒绝规则保持。
        const auto options = wifi_demo::parseOptions(argc, argv);
        const auto maximum = options.maximum;
        const auto port = options.input_port;
        const auto rtsp = options.rtsp_port;
        out = options.output;
        need(!fs::exists(out) && fs::create_directory(out), "Fresh demo output directory required");
        lifecycle.open(out / "lifecycle.jsonl");
        auto state = [&](const char* e) {
            lifecycle << "{\"event\":\"" << e << "\",\"board_ns\":" << now() << "}\n";
            lifecycle.flush();
            need(bool(lifecycle), "Lifecycle write failed");
        };
        // 2. 子进程先启动，主线程随后创建Engine；设备描述符不传给显示子进程。
        const auto began = now();
        display = std::make_unique<pose::display::Process>(fs::canonical(argv[0]).parent_path() / "pose_display_worker", out / "display");
        video = std::make_unique<wifi_demo::Video>(* display, out / "video", unsigned(rtsp));
        video->waitCapture();
        state("VPU_actual_capture");
        video->beginInitialization();
        engine = std::make_unique<wifi_demo::Engine>(options.model, out / "engine");
        video->initialized();
        state("Engine_created_main_thread");
        input = std::make_unique<pose_v1::transport::Receiver>(options.bind, uint16_t(port), 5000, 1);
        {
            std::ofstream f(out / "input.ready");
            f << port << '\n';
            need(bool(f), "Input ready write failed");
        }

        std::cout << "DEMO_INPUT_READY " << port << " RTSP rtsp://192.168.126.49:" << rtsp << "/pose\n" << std::flush;
        const auto ready = now();
        // 3. 消费完整拥有值窗口，先保存原结果，再发布视频姿态。
        while (results.size() < maximum) {
            video->check();
            input->check();
            need(!input->stats().rejected, "CSI record rejected");
            need(now() - began < 170000000000ULL, "Demo total budget exceeded");
            auto item = input->pop(std::chrono::milliseconds(100));
            if (!item) {
                if (input->finished()) break;
                need(results.size() || now() - ready < 60000000000ULL, "Demo input startup timeout");
                continue;
            }
            const auto arrived = std::chrono::duration_cast<std::chrono::nanoseconds>(item->arrived.time_since_epoch()).count();
            auto r = engine->process_window(item->window);
            const auto returned = now();
            pose::display::Pose p;
            p.frame = r.frame_id;
            p.invocation = r.invocation;
            p.scores = r.scores;
            p.poses = r.poses;
            p.publishedNs = returned;
            results.add(std::move(item->window), std::move(r), uint64_t(arrived), returned);
            video->publish(std::move(p));
        }

        input->stop();
        input->check();
        const auto counters = input->stats();
        received = counters.received;
        overwritten = counters.overwritten;
        need(!counters.rejected && results.size() > 0, "No valid completed demo frames");
        state("production_stopped");
    } catch (...) {
        failure = std::current_exception();
        if (input) input->stop();
        if (video) video->abort(failure);
    }

    // 4. 先结束视频工作线程，再释放输入、视频和显示对象。
    if (video) {
        try {
            video->finish();
        } catch (...) {
            if (!failure) failure = std::current_exception();
        }

    }

    input.reset();
    video.reset();
    display.reset();
    if (lifecycle) {
        lifecycle << "{\"event\":\"workers_joined\",\"board_ns\":" << now() << "}\n";
        lifecycle.flush();
    }

    // 5. 保存全部已拥有结果和诊断；保存失败不覆盖更早的原错误。
    if (!out.empty() && fs::is_directory(out)) {
        auto attempt = [&](auto f) {
            try {
                f();
            } catch (...) {
                if (!failure) failure = std::current_exception();
            }
        };
        attempt([&] {
            results.save(out / "results");
        });
        attempt([&] {
            if (engine) engine->save_evidence();
        });
    }

    // 6. 所有工作线程已join，最后释放主线程Engine。
    engine.reset();
    if (lifecycle) {
        lifecycle << "{\"event\":\"Engine_destroyed\",\"board_ns\":" << now() << "}\n";
        lifecycle.flush();
    }

    try {
        if (!out.empty() && fs::is_directory(out)) {
            std::ofstream f(out / "summary.json");
            f << "{\"completed\":" << results.size() << ",\"received\":" << received << ",\"overwritten\":" << overwritten <<
            ",\"workers_joined_before_Engine_destroyed\":true,\"RTSP\":true,\"HDMI\":false,\"failed\":" << (failure ? "true" : "false") <<
            "}\n";
            need(bool(f), "Summary save failed");
        }

        if (failure) std::rethrow_exception(failure);
        std::cout << "Demo completed " << results.size() << " real CSI windows\n";
        return 0;
    } catch (const std::exception& e) {
        if (!out.empty() && fs::is_directory(out)) {
            std::ofstream f(out / "failure.txt");
            f << e.what() << '\n';
        }

        std::cerr << "DEMO_STOP: " << e.what() << '\n';
        return 1;
    }

}
