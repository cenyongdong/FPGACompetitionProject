// 独立有限诊断入口：保存完整实际值后逐位比较，异常永久停止唯一Engine。
#include "application_core.hpp"
#include "application_clock.hpp"
#include "sdk_profile.hpp"
#include "host_failure_evidence.hpp"
#include "failure_source_readback.hpp"
#include "host_stage_observation.hpp"
#include "producer_count_observation.hpp"
#include "tensor_identity_observation.hpp"
#include <cmath>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>

namespace {
    namespace fs = std::filesystem;
    namespace app = pose_v1::application;
    namespace fc = pose_v1::forward_clock;

    void need(bool value, const char* message) {
        if (!value) throw std::runtime_error(message);
    }

    template<class T> T read_array(const fs::path& path) {
        need(fs::file_size(path) == sizeof(T), "Reference length differs");
        T result{};
        std::ifstream in(path, std::ios::binary);
        need(bool(in.read(reinterpret_cast<char*>(result.data()), sizeof(T))), "Reference read failed");
        for (float value : result) need(std::isfinite(value), "Reference is non-finite");
        return result;
    }

    template<class T> void save_array(const fs::path& path, const T& value) {
        std::ofstream out(path, std::ios::binary);
        out.write(reinterpret_cast<const char*>(value.data()), sizeof(T));
        need(bool(out), "Actual output save failed");
    }

    struct Case {
        std::string name;
        pose_v1::Window window;
        pose_v1::Tokens input;
        std::array<float, 100> scores;
        std::array<float, 4200> poses;
    };

    std::vector<Case> load_cases(const fs::path& package) {
        const char* names[] = {"S11_01_308", "S11_01_309", "S11_01_310"};
        std::vector<Case> cases;
        for (const auto* name : names) {
            const auto stem = package / "fixtures" / name;
            Case c;
            c.name = name;
            c.window = pose_v1::read_window(stem.string() + ".csi");
            c.input = read_array<pose_v1::Tokens>(stem.string() + ".input.f32");
            c.scores = read_array<std::array<float, 100>>(stem.string() + ".scores.f32");
            c.poses = read_array<std::array<float, 4200>>(stem.string() + ".poses.f32");
            cases.push_back(std::move(c));
        }
        return cases;
    }

    std::string quote(const std::string& value) {
        std::ostringstream out;
        out << '"';
        for (unsigned char c : value) {
            if (c == '"' || c == '\\') out << '\\' << c;
            else if (c < 32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
            else out << c;
        }
        return out.str() + '"';
    }

    double elapsed(fc::Clock::time_point begin) {
        return std::chrono::duration<double, std::milli>(fc::Clock::now() - begin).count();
    }

    // 每个模块独立保存；保存失败也不替换原推理/比较错误。
    void save_diagnostics(app::Engine* engine, const fs::path& output) {
        std::exception_ptr first;
        auto save = [&](auto task) {
            try { task(); } catch (...) { if (!first) first = std::current_exception(); }
        };
        if (engine) save([&] { engine->save_evidence(); });
        // 构造失败时也可保存初始化的部分时间线。
        save([&] { fc::save(output / "monotonic-spans.jsonl"); });
        save([&] { fc::save_transfers(output / "transfers.jsonl"); });
        save([&] { pose_v1::timing_sdk::save(output); });
        save([] { pose::stage_observation::saveMetadata(); });
        save([] { pose::producer_count::save(); });
        save([] { pose::tensor_identity::save(); });
        if (first) std::rethrow_exception(first);
    }
}

int main(int argc, char** argv) {
    fs::path package, output;
    std::string mode = "wall";
    size_t cycles = 1, completed = 0;
    bool allow = false;
    bool owns_output = false;
    std::unique_ptr<app::Engine> engine;
    try {
        for (int i = 1; i < argc; ++i) {
            const std::string key = argv[i];
            if (key == "--allow-device-init") { allow = true; continue; }
            need(i + 1 < argc, "Missing option value");
            const std::string value = argv[++i];
            if (key == "--package") package = value;
            else if (key == "--output") output = value;
            else if (key == "--mode") mode = value;
            else if (key == "--cycles") {
                need(!value.empty() && value.find_first_not_of("0123456789") == std::string::npos, "Invalid cycle count");
                cycles = std::stoul(value);
            } else throw std::runtime_error("Unknown timing option");
        }
        need(allow && !package.empty() && !output.empty(), "Explicit package/output/device flag required");
        need(cycles >= 1 && cycles <= 8, "Budget: 1..8 cycles, at most24 forwards");
        need(mode == "baseline" || mode == "wall" || mode == "sdk", "Unknown timing mode");
        need(!fs::exists(output), "Preserve prior run; fresh output required");
        need(fs::create_directory(output), "Fresh output directory creation failed");
        owns_output = true;
        fs::create_directory(output / "engine");
        // 在打开设备之前读完并核验三份参考；文件IO不计入Engine处理时间。
        const auto cases = load_cases(package);
        fc::configure(mode == "baseline" ? 0 : cases.size() * cycles);
        pose_v1::timing_sdk::configure(mode == "sdk");
        pose::failure_evidence::configure(output / "failed-host-inputs");
        pose::source_diagnostic::configure(output / "failed-host-inputs/source-readback");
        pose::stage_observation::configure(output / "copy-observations");
        pose::producer_count::configure(output / "producer-counts");
        pose::tensor_identity::configure(output / "tensor-identities");
        app::Config config;
        config.graph = package / "models/piw24_ZG.json";
        config.raw = package / "models/piw24_ZG.raw";
        config.evidence = output / "engine";
        config.allow_device_init = true;
        config.minimal_log = true;
        config.diagnostic_frames = 0;
        config.timing_frames = mode == "baseline" ? 0 : cases.size() * cycles;
        engine = std::make_unique<app::Engine>(config);
        std::ofstream results(output / "frames.jsonl");
        results << std::setprecision(17);
        for (size_t cycle = 0; cycle < cycles; ++cycle) {
            for (const auto& c : cases) {
                const auto actual = engine->process_window_checked(c.window, c.name, c.input);
                const auto folder = output / ("frame-" + std::to_string(actual.invocation));
                fs::create_directory(folder);
                auto start = fc::Clock::now();
                save_array(folder / "input.f32", actual.input);
                save_array(folder / "scores.f32", actual.scores);
                save_array(folder / "poses.f32", actual.poses);
                const auto save_ms = elapsed(start);
                // 先保存完整实际输出，再比较；失配停止，晚源不修补结果。
                start = fc::Clock::now();
                const bool matched = std::memcmp(actual.scores.data(), c.scores.data(), sizeof(c.scores)) == 0 &&
                                     std::memcmp(actual.poses.data(), c.poses.data(), sizeof(c.poses)) == 0;
                const auto compare_ms = elapsed(start);
                results << "{\"case\":" << quote(c.name) << ",\"mode\":" << quote(mode)
                        << ",\"invocation\":" << actual.invocation << ",\"cycle\":" << cycle
                        << ",\"frame_id\":" << actual.frame_id << ",\"matched\":" << (matched ? "true" : "false")
                        << ",\"process_ms\":" << actual.process_ms << ",\"preprocess_ms\":" << actual.preprocess_ms
                        << ",\"input_prepare_ms\":" << actual.prepare_ms << ",\"state_clear_ms\":" << actual.state_clear_ms
                        << ",\"forward_ms\":" << actual.forward_ms << ",\"final_wait_ms\":" << actual.final_wait_ms
                        << ",\"output_read_ms\":" << actual.output_ms << ",\"selection_ms\":" << actual.selection_ms
                        << ",\"process_cpu_ms\":" << actual.cpu_ms << ",\"actual_save_ms\":" << save_ms
                        << ",\"comparison_ms\":" << compare_ms << ",\"completed_layers\":" << actual.completed_layers
                        << ",\"host_callbacks\":" << actual.host_callbacks << ",\"zg_callbacks\":" << actual.zg_callbacks << "}\n";
                results.flush();
                need(bool(results), "Frame results write failed");
                need(matched, "Complete output differs; stop without retry");
                ++completed;
                // SDK内部分析/计时器读取不计入process_ms，单独记录collection_ms。
                engine->collect_timing_profile();
            }
        }
        save_diagnostics(engine.get(), output);
        const auto init_ms = engine->init_ms();
        engine.reset();
        std::ofstream summary(output / "summary.json");
        summary << std::setprecision(17) << "{\"status\":\"finite_numeric_run_completed\",\"mode\":" << quote(mode)
                << ",\"planned_frames\":" << cases.size() * cycles << ",\"completed_frames\":" << completed
                << ",\"init_ms\":" << init_ms
                << ",\"pure_NPU_compute_ns\":null,\"DDR_stall_ns\":null,\"exact_SDK_dispatch_ns\":null"
                << ",\"VPU_or_TCP_load\":false,\"old_DATA_investigation_resumed\":false,\"engine_destroyed\":true}\n";
        need(bool(summary), "Summary write failed");
        std::cout << "Finite timing run completed: " << completed << " frames; further analysis required\n";
        return 0;
    } catch (const std::exception& error) {
        std::string diagnostic_error;
        if (owns_output) {
            try { save_diagnostics(engine.get(), output); }
            catch (const std::exception& e) { diagnostic_error = e.what(); }
            engine.reset();
            std::ofstream failure(output / "failure.json");
            failure << "{\"status\":\"failed_stop_no_retry\",\"completed_frames\":" << completed
                    << ",\"error\":" << quote(error.what()) << ",\"diagnostic_error\":" << quote(diagnostic_error) << "}\n";
        }
        std::cerr << error.what() << '\n';
        return 1;
    }
}
