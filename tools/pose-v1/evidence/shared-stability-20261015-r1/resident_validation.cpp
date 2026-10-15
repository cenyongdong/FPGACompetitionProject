#include "resident_support.hpp"

namespace {
    class OutputStream {
        std::ofstream inputs_, scores_, poses_;
    public:
        explicit OutputStream(const fs::path& root)
            : inputs_(root / "inputs.f32", std::ios::binary),
              scores_(root / "scores.f32", std::ios::binary),
              poses_(root / "poses.f32", std::ios::binary) {
            need(bool(inputs_) && bool(scores_) && bool(poses_), "Output stream open failed");
        }
        void save(const app::Result& r) {
            inputs_.write(reinterpret_cast<const char*>(r.input.data()), sizeof(r.input)); inputs_.flush();
            scores_.write(reinterpret_cast<const char*>(r.scores.data()), sizeof(r.scores)); scores_.flush();
            poses_.write(reinterpret_cast<const char*>(r.poses.data()), sizeof(r.poses)); poses_.flush();
            need(bool(inputs_) && bool(scores_) && bool(poses_), "Complete actual output stream write failed");
        }
    };
    void progress(const fs::path& path, size_t completed, double elapsed_ms) {
        const auto temporary = path.string() + ".tmp";
        std::ofstream out(temporary);
        out << std::setprecision(17) << "{\"completed\":" << completed << ",\"elapsed_ms\":" << elapsed_ms << "}\n";
        out.close(); need(bool(out), "Progress write failed");
        fs::rename(temporary, path);
    }
    size_t integer(const std::string& s) {
        need(!s.empty() && s.find_first_not_of("0123456789") == std::string::npos, "Invalid unsigned option");
        return std::stoull(s);
    }
}

int main(int argc, char** argv) {
    fs::path package, output;
    size_t seconds = 0, max_frames = 0, completed = 0, saved = 0;
    bool allow = false, owns = false;
    std::unique_ptr<app::Engine> engine;
    try {
        for (int i = 1; i < argc; ++i) {
            std::string key = argv[i];
            if (key == "--allow-device-init") { allow = true; continue; }
            need(i+1 < argc, "Missing option value");
            std::string value = argv[++i];
            if (key == "--package") package=value;
            else if (key == "--output") output=value;
            else if (key == "--seconds") seconds=integer(value);
            else if (key == "--max-frames") max_frames=integer(value);
            else throw std::runtime_error("Unknown resident option");
        }
        need(allow && !package.empty() && !output.empty(), "Explicit device/package/output authorization required");
        need(seconds>0 && seconds<=1800 && max_frames>0 && max_frames<=90000, "Resident phase budget differs");
        need(!fs::exists(output) && fs::create_directory(output), "Fresh output required; no retry");
        owns=true; fs::create_directory(output/"engine");
        const auto cases=load_cases(package);
        fc::configure(3);
        pose_v1::timing_sdk::configure(false);
        pose::failure_evidence::configure(output/"failed-host-inputs");
        pose::source_diagnostic::configure(output/"failed-host-inputs/source-readback");
        pose::stage_observation::configure(output/"copy-observations");
        pose::producer_count::configure(output/"producer-counts");
        pose::tensor_identity::configure(output/"tensor-identities");
        app::Config config;
        config.graph=package/"models/piw24_shared_ZG.json";
        config.raw=package/"models/piw24_shared_ZG.raw";
        config.evidence=output/"engine";config.allow_device_init=true;
        config.minimal_log=true;config.diagnostic_frames=0;config.timing_frames=3;
        engine=std::make_unique<app::Engine>(config);
        OutputStream actual_stream(output);
        std::ofstream frames(output/"frames.jsonl");frames<<std::setprecision(17);
        std::ofstream init(output/"initialized.json");
        init<<"{\"init_ms\":"<<std::setprecision(17)<<engine->init_ms()<<"}\n";init.close();
        need(bool(init), "Initialization record write failed");
        const auto began=fc::Clock::now();
        progress(output/"progress.json",0,0);
        while (completed<max_frames && elapsed(began)<seconds*1000.0) {
            const auto& c=cases[completed%cases.size()];
            const auto actual=engine->process_window_checked(c.window,c.name,c.input);
            need(actual.invocation==completed, "Invocation progression differs");
            const auto saving=fc::Clock::now();actual_stream.save(actual);++saved;
            const auto save_ms=elapsed(saving);const auto comparing=fc::Clock::now();
            const auto gate=pose::shared_output_gate::compare(actual.scores,c.scores,actual.poses,c.poses,3.0,0.2f);
            const auto comparison_ms=elapsed(comparing);
            frames<<"{\"invocation\":"<<actual.invocation<<",\"case\":"<<quote(c.name)
                  <<",\"matched\":"<<(gate.accepted?"true":"false")
                  <<",\"finite\":"<<(gate.finite?"true":"false")
                  <<",\"scores_bitwise_equal\":"<<(gate.scores_bitwise_equal?"true":"false")
                  <<",\"poses_bitwise_equal\":"<<(gate.poses_bitwise_equal?"true":"false")
                  <<",\"checked_candidates\":"<<gate.checked_candidates
                  <<",\"max_checked_joint_delta_mm\":"<<gate.max_checked_joint_delta_mm
                  <<",\"max_all_joint_delta_mm\":"<<gate.max_joint_delta_mm
                  <<",\"excluded_over_limit_joints\":"<<gate.excluded_over_limit_joints
                  <<",\"process_ms\":"<<actual.process_ms<<",\"preprocess_ms\":"<<actual.preprocess_ms
                  <<",\"forward_ms\":"<<actual.forward_ms<<",\"final_wait_ms\":"<<actual.final_wait_ms
                  <<",\"output_read_ms\":"<<actual.output_ms<<",\"cpu_ms\":"<<actual.cpu_ms
                  <<",\"save_ms\":"<<save_ms<<",\"comparison_ms\":"<<comparison_ms
                  <<",\"completed_layers\":"<<actual.completed_layers
                  <<",\"host_callbacks\":"<<actual.host_callbacks<<",\"zg_callbacks\":"<<actual.zg_callbacks<<"}\n";
            frames.flush();need(bool(frames), "Frame record write failed");
            need(gate.accepted, "Confidence3mm/complete score/finite gate failed; stop without retry");
            engine->collect_timing_profile();++completed;
            if (completed%16==0) progress(output/"progress.json",completed,elapsed(began));
        }
        const auto duration=elapsed(began);
        progress(output/"progress.json",completed,duration);
        save_diagnostics(engine.get(),output);engine.reset();
        const bool complete_duration=duration>=seconds*1000.0;
        std::ofstream summary(output/"summary.json");
        summary<<std::setprecision(17)<<"{\"status\":\""<<(complete_duration?"resident_duration_completed":"frame_cap_reached_before_duration")
               <<"\",\"completed\":"<<completed<<",\"saved\":"<<saved<<",\"seconds_budget\":"<<seconds
               <<",\"max_frames\":"<<max_frames<<",\"actual_duration_ms\":"<<duration
               <<",\"unique_input_sources\":3,\"engine_destroyed\":true,\"diagnostic_sample_frames\":3}\n";
        summary.close();need(bool(summary), "Summary write failed");
        return complete_duration?0:2;
    } catch (const std::exception& error) {
        std::string diagnostic_error;
        if (owns) {
            try {save_diagnostics(engine.get(),output);} catch(const std::exception& e) {diagnostic_error=e.what();}
            engine.reset();
            std::ofstream failure(output/"failure.json");
            failure<<"{\"status\":\"failed_stop_no_retry\",\"completed\":"<<completed<<",\"saved\":"<<saved
                   <<",\"error\":"<<quote(error.what())<<",\"diagnostic_error\":"<<quote(diagnostic_error)<<"}\n";
        }
        std::cerr<<error.what()<<'\n';return 1;
    }
}
