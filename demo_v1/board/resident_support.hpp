#pragma once
// 独立有限诊断入口：保存完整实际值后执行用户批准的3mm门检，异常停止。
#include "application_core.hpp"
#include "shared_output_gate.hpp"
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

