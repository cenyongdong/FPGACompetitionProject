#include "resident_sequence.hpp"
#include "model_only_run.hpp"
#include "model_load_lifecycle.hpp"
#include "picture_vpu.hpp"
#include "skeleton_render.hpp"
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
void need(bool ok,const char* why){if(!ok){throw std::runtime_error(why);}}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
std::ofstream file(const fs::path& p){std::ofstream f(p);need(bool(f),"Resident evidence open failed");return f;}
struct Stamp {size_t invocation,phase,local;uint64_t scheduled,begin,end=0,verified=0;};
struct Phase {
    size_t offset;model::Run run;
    Phase(size_t start,std::vector<proof::FixtureWindow> cases,size_t limit):offset(start),run(std::move(cases),limit){}
};
void saveReturned(const std::vector<std::unique_ptr<Phase>>& phases,const fs::path& out){
    auto index=file(out/"returned-index.jsonl");
    for(size_t phase=0;phase<phases.size();++phase){const auto& p=*phases[phase];for(const auto& r:p.run.returned()){
        const auto global=p.offset+r.attempt.index;
        index<<"{\"invocation\":"<<global<<",\"phase\":"<<phase<<",\"local_index\":"<<r.attempt.index<<",\"frame_id\":"<<r.result.frame_id<<",\"fixture_frame_id\":"<<r.attempt.fixtureFrame<<",\"case\":"<<std::quoted(r.attempt.caseName)<<",\"verified\":"<<(r.verified?"true":"false")<<"}\n";
        if(!r.verified){const auto d=out/("unverified-owned-"+std::to_string(global));fs::create_directory(d);
            proof::persistBytes(d/"input.f32",r.result.input.data(),sizeof(r.result.input));proof::persistBytes(d/"scores.f32",r.result.scores.data(),sizeof(r.result.scores));proof::persistBytes(d/"poses.f32",r.result.poses.data(),sizeof(r.result.poses));}
    }}index.close();need(bool(index),"Resident returned index save failed");
}
int run(int argc,char** argv){
    need(argc==6&&std::string(argv[3])=="--finite-check"&&std::string(argv[4])=="--allow-device-init"&&std::string(argv[5])=="--allow-vpu-stream","PACKAGE FRESH-RESULTS --finite-check --allow-device-init --allow-vpu-stream");
    const fs::path package=argv[1],out=argv[2];need(!fs::exists(out),"Preserve resident evidence");fs::create_directory(out);
    auto base=proof::fixtureWindows(package,false),expanded=proof::fixtureWindows(package,true);expanded.pop_back();
    std::vector<std::unique_ptr<Phase>> phases;phases.push_back(std::make_unique<Phase>(0,std::move(base),4));phases.push_back(std::make_unique<Phase>(4,std::move(expanded),103));
    pose::resident_sequence::Sequence sequence;std::vector<Stamp> stamps;stamps.reserve(107);
    auto life=file(out/"lifecycle.jsonl"),stages=file(out/"stages.jsonl"),calls=file(out/"inference.jsonl");
    fs::create_directory(out/"pictures");
    std::array<float,100> emptyScores{};std::array<float,4200> emptyPoses{};
    auto noInput=pose_v1::render::draw(emptyScores,emptyPoses,0,pose_v1::render::Status::NoInput);
    pose::video::OwnedFrame warm;warm.nv12=pose_v1::render::yuv420sp(noInput.rgb,1280,720,false);warm.generatedNs=now();warm.inferenceResult=false;
    proof::persistBytes(out/"pictures/warmup.nv12",warm.nv12.data(),warm.nv12.size());
    auto pictures=file(out/"pictures/index.jsonl");
    const auto entry=now();std::unique_ptr<app::Engine> engine;std::unique_ptr<pose::picture::Vpu> video;std::exception_ptr failure;
    auto hostFrame=std::make_shared<pose::invocation_evidence::Frame>();size_t phaseIndex=0;bool engineCreated=false;
    pose::load_lifecycle::Control load(true,{
        [&]{video=std::make_unique<pose::picture::Vpu>(out/"vpu",std::move(warm));},
        [&]{video->waitReady();life<<"{\"event\":\"VPU_actual_capture\",\"time_ns\":"<<now()<<"}\n";life.flush();},
        [&]{if(video){video->check();}},[&]{if(video){video->join();}},[&](bool abort){if(video){video->requestStop(abort);}}
    });
    fs::create_directory(out/"engine");
    pose::stage_observation::configure(out/"copy-observations",[hostFrame](uint64_t frame,uint64_t inv,int64_t op,size_t slot,std::vector<char> bytes){hostFrame->begin(frame,inv);hostFrame->record(op,slot,std::move(bytes));});
    pose::producer_count::configure(out/"producer-counts");pose::tensor_identity::configure(out/"tensor-identities");
    pose::failure_evidence::configure(out/"failed-host-inputs");pose::source_diagnostic::configure(out/"failed-host-inputs/source-readback");
    try{
        load.start();
        app::Config cfg;cfg.graph=package/"graph/piw24_ZG.json";cfg.raw=package/"graph/piw24_ZG.raw";cfg.evidence=out/"engine";cfg.allow_device_init=true;cfg.minimal_log=true;cfg.diagnostic_frames=0;cfg.timing_frames=0;
        const auto init=now();engine=std::make_unique<app::Engine>(cfg);engineCreated=true;const auto ready=now();need(ready-init<60000000000ULL,"Resident Engine init exceeds60s");
        life<<std::setprecision(17)<<"{\"event\":\"Engine_created\",\"time_ns\":"<<ready<<",\"init_ms\":"<<engine->init_ms()<<",\"Engine_object\":"<<reinterpret_cast<uintptr_t>(engine.get())<<"}\n";life.flush();
        for(phaseIndex=0;phaseIndex<phases.size();++phaseIndex){
            load.check();const auto spec=sequence.begin();auto& p=*phases[phaseIndex];need(p.offset==spec.offset,"Resident phase offset mismatch");const auto epoch=now();uint64_t previous=0;
            stages<<"{\"event\":\"stage_started\",\"phase\":"<<phaseIndex<<",\"name\":"<<std::quoted(spec.name)<<",\"offset\":"<<spec.offset<<",\"count\":"<<spec.count<<",\"period_ns\":"<<spec.period<<",\"time_ns\":"<<epoch<<",\"Engine_object\":"<<reinterpret_cast<uintptr_t>(engine.get())<<",\"VPU_object\":"<<reinterpret_cast<uintptr_t>(video.get())<<"}\n";stages.flush();
            for(size_t local=0;local<spec.count;++local){
                load.check();const auto global=sequence.invocation();const auto scheduled=model::scheduledStart(epoch,local,previous,spec.period);
                std::this_thread::sleep_until(std::chrono::steady_clock::time_point(std::chrono::nanoseconds(scheduled)));load.check();
                const auto begin=now();need(begin-entry<180000000000ULL,"Resident total budget exceeds180s");previous=begin;stamps.push_back(Stamp{global,phaseIndex,local,scheduled,begin});
                p.run.step([&](const auto& w){auto actual=w;actual.frame_id=100000+global;auto r=engine->process_window(actual);stamps.back().end=now();return r;},[&](const auto& c,const auto& r){
                    auto actual=r.attempt.window;actual.frame_id=100000+global;auto fixture=c;fixture.window.frame_id=actual.frame_id;
                    proof::saveThenVerifyResult(fixture,r.result,actual,global,out,calls);stamps.back().verified=now();load.check();
                    const auto drawBegin=now();auto rgb=pose_v1::render::draw(r.result.scores,r.result.poses,r.result.frame_id);
                    need(rgb.top_index==r.result.best_index,"Picture highest candidate differs");
                    for(const auto& point:rgb.projected){need(point[1]<590,"Joint intersects encoded marker");}
                    const auto drawEnd=now();pose::video::OwnedFrame frame;frame.nv12=pose_v1::render::yuv420sp(rgb.rgb,1280,720,false);
                    frame.sourceFrame=r.result.frame_id;frame.invocation=global;frame.generatedNs=now();
                    const auto name="result"+std::to_string(global)+".nv12";
                    proof::persistBytes(out/"pictures"/name,frame.nv12.data(),frame.nv12.size());
                    pictures<<"{\"invocation\":"<<global<<",\"frame_id\":"<<frame.sourceFrame<<",\"case\":"<<std::quoted(c.name)<<",\"file\":"<<std::quoted(name)<<",\"bytes\":"<<frame.nv12.size()<<",\"best_index\":"<<rgb.top_index<<",\"draw_begin_ns\":"<<drawBegin<<",\"draw_end_ns\":"<<drawEnd<<",\"convert_end_ns\":"<<frame.generatedNs<<",\"publish_begin_ns\":"<<now()<<"}\n";pictures.flush();need(bool(pictures),"Picture metadata write failed");
                    video->publish(std::move(frame));load.check();
                });sequence.completeCall();
            }
            stages<<"{\"event\":\"stage_completed\",\"phase\":"<<phaseIndex<<",\"offset\":"<<spec.offset<<",\"count\":"<<spec.count<<",\"time_ns\":"<<now()<<"}\n";stages.flush();load.check();sequence.advance();
        }
        need(sequence.done()&&now()-entry<180000000000ULL,"Resident sequence incomplete or timed out");
    }catch(...){sequence.stop();failure=std::current_exception();}
    load.finish(failure);need(load.joined(),"Resident worker not joined before Engine release");
    life<<"{\"event\":\"load_joined\",\"time_ns\":"<<now()<<",\"enabled\":true}\n";
    const bool failed=bool(failure);
    pose::invocation_evidence::flush({
        {"returned-owned",[&]{saveReturned(phases,out);}},
        {"timing-and-attempt",[&]{
            auto f=file(out/"timing.jsonl");for(const auto& s:stamps){f<<"{\"invocation\":"<<s.invocation<<",\"phase\":"<<s.phase<<",\"local_index\":"<<s.local<<",\"scheduled_ns\":"<<s.scheduled<<",\"process_begin_ns\":"<<s.begin<<",\"process_end_ns\":"<<s.end<<",\"verify_end_ns\":"<<s.verified<<"}\n";}f.close();need(bool(f),"Resident timing save failed");
            if(failed&&phaseIndex<phases.size()&&phases[phaseIndex]->run.current()){
                const auto& p=*phases[phaseIndex];const auto& a=*p.run.current();const auto d=out/"failed-attempt";fs::create_directory(d);proof::persistBytes(d/"raw-payload.bin",a.window.csi.data(),sizeof(a.window.csi));
                auto identity=file(d/"identity.json");identity<<"{\"phase\":"<<phaseIndex<<",\"invocation\":"<<p.offset+a.index<<",\"local_index\":"<<a.index<<",\"frame_id\":"<<100000+p.offset+a.index<<",\"fixture_frame_id\":"<<a.fixtureFrame<<",\"case\":"<<std::quoted(a.caseName)<<",\"owned_raw\":true}\n";
            }
        }},
        {"copy-metadata",[]{pose::stage_observation::saveMetadata();}},
        {"192-producer-counts",[]{pose::producer_count::save();}},
        {"tensor-object-identities",[]{pose::tensor_identity::save();}},
        {"Engine-evidence",[&]{if(engine){engine->save_evidence();}}},
        {"failed-Host-frame",[&]{if(failed&&hostFrame->inputs()){hostFrame->save(out/"failed-invocation-inputs");}}}
    },failure,out/"persistence-ledger.json");
    engine.reset();life<<"{\"event\":\""<<(engineCreated?"Engine_destroyed":"Engine_not_created_cleanup")<<"\",\"time_ns\":"<<now()<<"}\n";life.close();stages.close();pictures.close();need(bool(life)&&bool(stages)&&bool(pictures),"Resident lifecycle save failed");video.reset();
    size_t attempted=0,returned=0,correct=0;for(const auto& p:phases){attempted+=p->run.attempts();returned+=p->run.returned().size();for(const auto& r:p->run.returned()){correct+=r.verified;}}
    auto s=file(out/"summary.json");s<<"{\"mode\":\"picture-three-103\",\"expected\":107,\"attempted\":"<<attempted<<",\"returned\":"<<returned<<",\"correct\":"<<correct<<",\"passed\":"<<(!failure&&correct==107?"true":"false")<<",\"Engine_created\":"<<(engineCreated?"true":"false")<<",\"load_joined\":true,\"VPU\":true,\"sdk_profiling\":false,\"display\":false,\"network\":false,\"HDMI\":false}\n";s.close();need(bool(s),"Resident summary save failed");
    if(failure){std::rethrow_exception(failure);}std::cout<<"Resident three+103 completed107; one Engine and one owned-picture VPU lifecycle.\n";return 0;
}
}
int main(int argc,char** argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
