#include "core.hpp"
#include "io.hpp"
#include "journal.hpp"
#include "csi.hpp"
#ifdef POSE180_DEMO_SDK
#include "runtime.hpp"
#include "hdmi_output.hpp"
#include "hdmi_renderer.hpp"
#include "display_state.hpp"
#include "FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/software/source/display/r9_startup_observer.hpp"
#include "r9_observer_mapping.hpp"
#endif
#include <csignal>
#include <fstream>
#include <iostream>
#include <map>

namespace pd=pose180_demo;namespace pp=pose180_pipeline;namespace fs=std::filesystem;
namespace {
volatile std::sig_atomic_t stopping=0;
void stop(int){stopping=1;}
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
}
int main(int argc,char**argv) {
    std::signal(SIGINT,stop);std::signal(SIGTERM,stop);
    try {
        std::map<std::string,std::string> options;
        for(int i=1;i<argc;i+=2){need(i+1<argc,"Expected --option value");need(options.emplace(argv[i],argv[i+1]).second,"Repeated option");}
        auto take=[&](const char* key,const std::string& fallback){auto it=options.find(key);if(it==options.end())return fallback;auto v=it->second;options.erase(it);return v;};
        const fs::path package=take("--package","."),output=take("--output","");
        const auto bind=take("--bind","127.0.0.1"),csi_config=take("--csi","");
        const auto session=std::stoull(take("--session","0"));
        const auto seconds=std::stoul(take("--seconds","60"));
        const auto input_port=std::stoul(take("--input-port",csi_config.empty()?"39382":"0"));
        const auto result_port=std::stoul(take("--result-port","39383"));
        const auto status_port=std::stoul(take("--status-port","39384"));
        const auto max_age=std::stoull(take("--max-input-age-ms","500"))*1000000ull;
        const auto hdmi_arg=take("--hdmi","0");const bool hdmi=hdmi_arg=="1";
#ifdef POSE180_DEMO_SDK
        constexpr bool mock=false;
#else
        constexpr bool mock=true;
        const auto delay=std::stoul(take("--mock-delay-ms","10"));
        const auto slow_at=std::stoull(take("--mock-slow-at","0"));
        const auto fail_at=std::stoull(take("--mock-fail-at","0"));
        need(!hdmi,"Mock cannot access HDMI");
#endif
        need(options.empty(),"Unknown option");need(session && session<0xffffffffffff0000ull,"Explicit session required");
        need(input_port<=65535 && result_port>0 && result_port<=65535 && status_port>0 && status_port<=65535,"Port out of range");
        need(max_age>0 && max_age<=60000000000ull && (hdmi_arg=="0"||hdmi_arg=="1"),"Invalid age or HDMI option");
        need(csi_config.empty()||!input_port,"Use exactly one input adapter");
        need(!output.empty()&&!fs::exists(output)&&fs::create_directory(output),"Fresh output directory required");
        pd::Shared shared;
        // Must precede SDK, IO and CSI construction (fork cannot inherit them).
        pd::Journal journal(shared,output);
        pd::Io io(shared,bind,input_port,result_port,status_port,session,mock,hdmi);
        std::unique_ptr<pd::Csi> csi;
        if(!csi_config.empty())csi=std::make_unique<pd::Csi>(shared,csi_config,session);
        std::cout<<"RESIDENT_READY mock="<<mock<<" recorder_pid="<<journal.child_pid()<<std::endl;
#ifdef POSE180_DEMO_SDK
        std::unique_ptr<pp::Runtime> runtime;
        std::unique_ptr<pose::hdmi::Output> display;
        std::unique_ptr<Mapping> mapping;
        try {
            pp::Config config;config.graph=package/"models/piw24_pose180_ZG.json";
            config.raw=package/"models/piw24_pose180_ZG.raw";config.evidence=output/"engine";
            if(hdmi) {
                std::ifstream mode_file(package/"startup-mode.txt");std::string mode;mode_file>>mode;
                need(mode=="healthy"||mode=="consumed","Fresh same-boot startup admission required");
                // The deployment guard checks boot_id and candidate/SDK identities.
                mapping=std::make_unique<Mapping>();
                auto read=[&](unsigned at){return mapping->read(at);};
                auto write=[&](unsigned at,std::uint32_t n){mapping->write(at,n);};
                auto persist=[&](const std::string& line){journal.status(line);};
                pose::r9_startup::Observer observer(read,write,persist);
                auto before=observer.epoch("resident_before_Engine",4,[]{std::this_thread::sleep_for(std::chrono::milliseconds(20));});
                need(mode=="consumed"?pose::r9_startup::idle_after_drain(before,false):
                    pose::r9_startup::idle_healthy(before)&&before.words[4]==0,"Unhealthy pre-SDK return path");
                config.on_device_ready=[&](const icraft::xrt::Device& device){
                    display=std::make_unique<pose::hdmi::Output>(device,output/"hdmi.jsonl",&journal);
                    display->verifyMemory();
                };
                auto initialized=observer.epoch("resident_Engine_apply",6,[&]{runtime=std::make_unique<pp::Runtime>(config);});
                need(pose::r9_startup::return_path_healthy(initialized),"Initialization return path changed");
            } else runtime=std::make_unique<pp::Runtime>(config);
        }catch(const std::exception& error){shared.stats.isolated=true;journal.status(std::string("SDK initialization isolated: ")+error.what()+"\n");}
        pose::hdmi::PreparedBackground canvas;
        // Metadata only: the reusable pixel vector stays in canvas, so holding
        // the last actual pose adds no full-frame cache or model output copy.
        pose::hdmi::Rendered last_picture;
        std::uint64_t last_picture_id=0;
        pd::DisplayState presentation;
        if(hdmi)canvas.rgb565.resize(pose::hdmi::frameBytes);
        auto show=[&](pose::hdmi::Rendered& rendered) {
            const auto tag=presentation.next_tag();
            display->begin_show(rendered.rgb565,tag);
            canvas.rgb565=std::move(rendered.rgb565);
            // Same owner thread and adoption proof for hints and actual poses.
            while(!display->poll_show())std::this_thread::sleep_for(std::chrono::milliseconds(1));
            return tag;
        };
        auto show_wait=[&] {
            if(!hdmi || !display || shared.stats.isolated) return;
            const auto notice=presentation.hint(pd::now_ns(),shared.stats.resynchronizing,shared.stats.isolated);
            if(!notice) return;
            pose::hdmi::prepare_background(canvas);
            auto rendered=pose::hdmi::render_notice(std::move(canvas),
                notice->has_result?&last_picture:nullptr,last_picture_id,*notice);
            const auto tag=show(rendered);
            presentation.adopted_hint(*notice,pd::now_ns());
            shared.stats.display_updates=presentation.updates();
            shared.stats.display_hints=presentation.hints();
            const char* state=notice->kind==pose::hdmi::NoticeKind::Stale?"stale":
                notice->kind==pose::hdmi::NoticeKind::Resynchronizing?"resynchronizing":"waiting_input";
            journal.status("{\"event\":\"hdmi_hint\",\"tag\":"+std::to_string(tag)+
                ",\"state\":\""+state+"\""+
                ",\"has_result\":"+(notice->has_result?"true":"false")+
                ",\"result_age_seconds\":"+std::to_string(notice->age_seconds)+
                ",\"resynchronizing\":"+(notice->resynchronizing?"true":"false")+"}\n");
        };
#endif
        shared.stats.initialized=true;
        const auto started=pd::now_ns();auto last_status=started;
        pd::Input input;pp::Result result;pd::Record record{};std::uint64_t sequence=0;
        auto isolate=[&](const std::exception& error) {
            shared.stats.forward_start=0;shared.stats.isolated=true;shared.input.clear();shared.output.clear();
            journal.freeze();journal.status(std::string("isolated: ")+error.what()+"\n");
            // Keep listeners/status alive, never reopen or retry failed SDK.
        };
        while(!stopping && (!seconds || pd::now_ns()-started<seconds*1000000000ull)) {
            if(pd::now_ns()-last_status>1000000000ull){
                for(const auto& event:shared.stats.take_input_events())journal.diagnostic(event);
                journal.status(shared.stats.json(mock,hdmi));last_status=pd::now_ns();
            }
            if(shared.stats.isolated){std::this_thread::sleep_for(std::chrono::milliseconds(5));continue;}
            bool ready=shared.input.take(input);
            if(ready && (pd::now_ns()-input.arrived>max_age || input.epoch!=shared.stats.input_epoch)){
                ++shared.stats.stale;ready=false;
            }
            if(!ready) {
#ifdef POSE180_DEMO_SDK
                try{show_wait();}catch(const std::exception& error){isolate(error);}
#endif
                std::this_thread::sleep_for(std::chrono::milliseconds(5));continue;
            }
            const auto began=pd::now_ns();shared.stats.forward_start=began;
            try {
#ifdef POSE180_DEMO_SDK
                runtime->infer(input.window,result);
#else
                const auto invocation=shared.stats.inferred.load();
                std::this_thread::sleep_for(std::chrono::milliseconds(slow_at && invocation+1==slow_at?1500:delay));
                if(fail_at && invocation+1==fail_at)throw std::runtime_error("Injected mock SDK failure");
                result={};result.frame_id=input.window.frame_id;result.source_time_ns=input.window.source_time_ns;
                result.invocation=invocation;result.input=pose_v1::preprocess(input.window.csi);
                result.scores.fill(0.5f);result.poses.fill(float(invocation%100)/100);result.selected_pose.fill(result.poses[0]);
                result.finite_outputs=true;result.process_ms=double(pd::now_ns()-began)/1e6;
#endif
                const auto returned=pd::now_ns();shared.stats.forward_start=0;
                pp::encode_full(record,result,input.epoch,++sequence,input.arrived,began,returned,returned,1);
                journal.record(record); // Complete first values before validity checks.
                need(result.finite_outputs&&result.best_index<180,"Invalid output isolated");
                ++shared.stats.inferred;
                auto previous=shared.stats.last_result.exchange(returned);
                if(previous)shared.stats.longest_gap=std::max(shared.stats.longest_gap.load(),returned-previous);
                // Calls returning late are counted as real inference, not fresh display.
                if(returned-input.arrived>max_age || input.epoch!=shared.stats.input_epoch){
                    ++shared.stats.stale;
#ifdef POSE180_DEMO_SDK
                    show_wait();
#endif
                    continue;
                }
                if(shared.output.put(record))++shared.stats.pc_dropped;
#ifdef POSE180_DEMO_SDK
                if(hdmi) {
                    pose::hdmi::prepare_background(canvas);
                    auto rendered=pose::hdmi::render(std::move(canvas),result.scores.data(),result.poses.data(),180,result.frame_id);
                    show(rendered); // Prove adoption before another forward call.
                    last_picture=std::move(rendered);last_picture_id=result.frame_id;
                    const auto adopted=pd::now_ns();presentation.adopted_result(adopted);
                    ++shared.stats.adopted;shared.stats.last_adopt=adopted;
                    shared.stats.display_updates=presentation.updates();
                }
#endif
            }catch(const std::exception& error) {
                isolate(error);
            }
        }
        shared.stop=true;csi.reset();
#ifdef POSE180_DEMO_SDK
        // Output retains its unchanged tagged STOP/drain proof before any free.
        if(display){display->close();display.reset();}runtime.reset();
#endif
        for(const auto& event:shared.stats.take_input_events())journal.diagnostic(event);
        journal.status(shared.stats.json(mock,hdmi));
        // Single bounded completion receipt, written only after actual HDMI
        // STOP/drain and Runtime destruction. Polling liveness is not proof.
        { std::ofstream done(output/"completion.json");
          done<<"{\"native_shutdown_complete\":true,\"status\":"<<shared.stats.json(mock,hdmi)<<"}\n"; }
        std::cout<<shared.stats.json(mock,hdmi);
        return shared.stats.isolated?3:0;
    }catch(const std::exception& error){std::cerr<<"RESIDENT_STOP "<<error.what()<<std::endl;return 1;}
}
