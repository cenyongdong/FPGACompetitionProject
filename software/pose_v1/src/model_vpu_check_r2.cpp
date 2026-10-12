#include "model_only_run.hpp"
#include "model_load_lifecycle.hpp"
#include "scratch_vpu_load.hpp"
#include "presaved_result_evidence.hpp"
#include "host_failure_evidence.hpp"
#include "failure_source_readback.hpp"
#include "host_stage_observation.hpp"
#include "invocation_evidence.hpp"
#include "producer_count_observation.hpp"
#include "tensor_identity_observation.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <thread>
namespace {
namespace fs=std::filesystem;namespace app=pose_v1::application;namespace proof=pose::validation;namespace model=pose::model_only;
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
std::ofstream file(const fs::path&p){std::ofstream f(p);need(bool(f),"Model-only evidence open failed");return f;}
struct Stamp {size_t index;uint64_t scheduled,begin,end=0,verified=0;};
void saveReturnedIndex(const model::Run&run,const fs::path&out){
    auto index=file(out/"returned-index.jsonl");
    for(const auto&r:run.returned()){
        index<<"{\"invocation\":"<<r.attempt.index<<",\"frame_id\":"<<r.attempt.window.frame_id<<",\"fixture_frame_id\":"<<r.attempt.fixtureFrame<<",\"case\":"<<std::quoted(r.attempt.caseName)<<",\"verified\":"<<(r.verified?"true":"false")<<"}\n";
        if(!r.verified){
            // A separate fresh fallback never overwrites pre-gate bytes.
            const auto p=out/("unverified-owned-"+std::to_string(r.attempt.index));fs::create_directory(p);
            proof::persistBytes(p/"input.f32",r.result.input.data(),sizeof(r.result.input));proof::persistBytes(p/"scores.f32",r.result.scores.data(),sizeof(r.result.scores));proof::persistBytes(p/"poses.f32",r.result.poses.data(),sizeof(r.result.poses));
        }
    }index.close();need(bool(index),"Returned index save failed");
}
int run(int argc,char**argv){
    need(argc==7||argc==8,"model|model-vpu three|load-103 PACKAGE FRESH-RESULTS --finite-check --allow-device-init [--allow-vpu-stream]");
    const std::string loadMode=argv[1],mode=argv[2];const bool withVpu=loadMode=="model-vpu";
    const fs::path package=argv[3],out=argv[4];const bool expanded=mode=="load-103";
    need((loadMode=="model"||withVpu)&&(expanded||mode=="three")&&std::string(argv[5])=="--finite-check"&&std::string(argv[6])=="--allow-device-init"&&!fs::exists(out)&&(withVpu?argc==8&&std::string(argv[7])=="--allow-vpu-stream":argc==7),"Paired model/VPU permission differs");
    fs::create_directory(out);auto cases=proof::fixtureWindows(package,expanded);if(expanded){cases.pop_back();}
    const size_t count=expanded?103:4;const uint64_t period=expanded?200000000:500000000;
    model::Run bounded(std::move(cases),count);std::vector<Stamp>stamps;stamps.reserve(count);
    const auto entry=now();auto lifecycle=file(out/"lifecycle.jsonl"),calls=file(out/"inference.jsonl");
    std::unique_ptr<app::Engine>engine;std::exception_ptr failure;auto hostFrame=std::make_shared<pose::invocation_evidence::Frame>();
    std::unique_ptr<pose::scratch::VpuLoad>video;
    pose::load_lifecycle::Control load(withVpu,{
        [&]{video=std::make_unique<pose::scratch::VpuLoad>(out/"vpu");},
        [&]{video->waitReady();lifecycle<<"{\"event\":\"VPU_actual_capture\",\"time_ns\":"<<now()<<"}\n";lifecycle.flush();},
        [&]{if(video){video->check();}},
        [&]{if(video){video->join();}},
        [&](bool abort){if(video){video->requestStop(abort);}}
    });
    fs::create_directory(out/"engine");
    pose::stage_observation::configure(out/"copy-observations",[hostFrame](uint64_t frame,uint64_t inv,int64_t op,size_t slot,std::vector<char>bytes){hostFrame->begin(frame,inv);hostFrame->record(op,slot,std::move(bytes));});
    pose::producer_count::configure(out/"producer-counts");pose::tensor_identity::configure(out/"tensor-identities");
    pose::failure_evidence::configure(out/"failed-host-inputs");pose::source_diagnostic::configure(out/"failed-host-inputs/source-readback");
    try{
        load.start();
        app::Config cfg;cfg.graph=package/"graph/piw24_ZG.json";cfg.raw=package/"graph/piw24_ZG.raw";cfg.evidence=out/"engine";cfg.allow_device_init=true;cfg.minimal_log=true;cfg.diagnostic_frames=0;cfg.timing_frames=0;
        const auto init=now();engine=std::make_unique<app::Engine>(cfg);const auto ready=now();need(ready-init<60000000000ULL,"Model-only Engine init exceeds60s");
        lifecycle<<std::setprecision(17)<<"{\"event\":\"Engine_created\",\"time_ns\":"<<ready<<",\"init_ms\":"<<engine->init_ms()<<"}\n";lifecycle.flush();
        uint64_t previous=0;
        for(size_t i=0;i<count;++i){
            load.check();
            const auto scheduled=model::scheduledStart(ready,i,previous,period);
            std::this_thread::sleep_until(std::chrono::steady_clock::time_point(std::chrono::nanoseconds(scheduled)));
            load.check();
            const auto begin=now();need(begin-entry<180000000000ULL,"Model-only total budget exceeds180s");previous=begin;stamps.push_back(Stamp{i,scheduled,begin});
            bounded.step([&](const auto&w){auto r=engine->process_window(w);stamps.back().end=now();return r;},[&](const auto&c,const auto&r){
                auto fixture=c;fixture.window.frame_id=r.attempt.window.frame_id;
                proof::saveThenVerifyResult(fixture,r.result,r.attempt.window,r.attempt.index,out,calls);
                stamps.back().verified=now();load.check();
            });
        }
        need(now()-entry<180000000000ULL,"Model-only final budget exceeds180s");
    }catch(...){failure=std::current_exception();}
    load.finish(failure);
    need(load.joined(),"Load worker not joined before Engine release");
    lifecycle<<"{\"event\":\"load_joined\",\"time_ns\":"<<now()<<",\"enabled\":"<<(withVpu?"true":"false")<<"}\n";
    const bool computeFailed=bool(failure);
    pose::invocation_evidence::flush({
        {"returned-owned",[&]{saveReturnedIndex(bounded,out);}},
        {"timing-and-attempt",[&]{
            auto trace=file(out/"timing.jsonl");for(const auto&s:stamps){trace<<"{\"invocation\":"<<s.index<<",\"scheduled_ns\":"<<s.scheduled<<",\"process_begin_ns\":"<<s.begin<<",\"process_end_ns\":"<<s.end<<",\"verify_end_ns\":"<<s.verified<<"}\n";}trace.close();need(bool(trace),"Model-only timing save failed");
            if(computeFailed&&bounded.current()){
                const auto&a=*bounded.current();const auto p=out/"failed-attempt";fs::create_directory(p);proof::persistBytes(p/"raw-payload.bin",a.window.csi.data(),sizeof(a.window.csi));
                auto f=file(p/"identity.json");f<<"{\"invocation\":"<<a.index<<",\"frame_id\":"<<a.window.frame_id<<",\"fixture_frame_id\":"<<a.fixtureFrame<<",\"case\":"<<std::quoted(a.caseName)<<",\"owned_raw\":true}\n";
            }
        }},
        {"copy-metadata",[]{pose::stage_observation::saveMetadata();}},
        {"192-producer-counts",[]{pose::producer_count::save();}},
        {"tensor-object-identities",[]{pose::tensor_identity::save();}},
        {"Engine-evidence",[&]{if(engine){engine->save_evidence();}}},
        {"failed-Host-frame",[&]{if(computeFailed&&hostFrame->inputs()){hostFrame->save(out/"failed-invocation-inputs");}}}
    },failure,out/"persistence-ledger.json");
    engine.reset();lifecycle<<"{\"event\":\"Engine_destroyed\",\"time_ns\":"<<now()<<"}\n";lifecycle.close();need(bool(lifecycle),"Engine lifecycle save failed");
    video.reset();
    auto summary=file(out/"summary.json");size_t correct=0;for(const auto&r:bounded.returned()){correct+=r.verified;}
    summary<<"{\"mode\":"<<std::quoted(mode)<<",\"expected\":"<<count<<",\"attempted\":"<<bounded.attempts()<<",\"returned\":"<<bounded.returned().size()<<",\"correct\":"<<correct<<",\"passed\":"<<(!failure&&correct==count?"true":"false")<<",\"period_ns\":"<<period<<",\"Engine_stopped_after_error\":"<<(bounded.stopped()?"true":"false")<<",\"sdk_profiling\":false,\"VPU\":"<<(withVpu?"true":"false")<<",\"load_joined\":true,\"display\":false,\"network\":false,\"HDMI\":false,\"NPU_forward\":true}\n";summary.close();need(bool(summary),"Model-only summary save failed");
    if(failure){std::rethrow_exception(failure);}std::cout<<"Model-only "<<mode<<" completed "<<correct<<"; synthetic VPU="<<withVpu<<"; no display/network.\n";return 0;
}
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
