// Finite orchestration: main-owned Engine, encoding worker, event-loop worker.
// All math, SDK completion/copies, renderer and VPU protocol remain in modules.
#include "pipeline_fixture_source.hpp"
#include "video_frame_marker.hpp"
#include "skeleton_render.hpp"
#include "resident_frame_queue.hpp"
#include "vpu_resident_encoder.hpp"
#include "online_rtsp.hpp"
#include "tcp_window_input.hpp"
#include <cstring>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <iomanip>
#include <iostream>
#include <thread>

namespace {
using Clock=std::chrono::steady_clock;namespace fs=std::filesystem;
namespace app=pose_v1::application;namespace rr=pose_v1::render;namespace vv=pose::video;namespace net=pose::stream;namespace proof=pose::validation;
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
uint64_t ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
std::ofstream trace(const fs::path& p){std::ofstream f(p);check(bool(f),"Live evidence open failed");return f;}
int run(int argc,char**argv){
    check(argc==5||argc==8,"Usage: host-check|live-three|live-27 PACKAGE FRESH-RESULTS --finite-check [--allow-device-init --allow-vpu-stream --allow-network]");
    const std::string mode=argv[1];const fs::path package=argv[2],out=argv[3];const bool host=mode=="host-check";
    check(host||mode=="live-three"||mode=="live-27","Unknown live mode");check(std::string(argv[4])=="--finite-check"&&!fs::exists(out),"Preserve evidence / explicit finite check");
    check((argc==8)==!host,"Hardware/network authorization differs");
    if(!host)check(std::string(argv[5])=="--allow-device-init"&&std::string(argv[6])=="--allow-vpu-stream"&&std::string(argv[7])=="--allow-network","Explicit hardware/network flags required");
    fs::create_directory(out);
    if(host){proof::validatedHostGate(package,out);auto f=trace(out/"summary.json");f<<"{\"stage\":\"host-check\",\"cases\":107,\"device_opened\":false,\"VPU_streamed\":false}\n";return 0;}
    auto cases=proof::fixtureWindows(package,mode=="live-27");fs::create_directory(out/"engine");fs::create_directory(out/"frames");
    auto calls=trace(out/"inference.jsonl"),samples=trace(out/"samples.jsonl"),packets=trace(out/"packets.jsonl"),lifecycle=trace(out/"lifecycle.jsonl"),auLog=trace(out/"access-units.jsonl");
    vv::ResidentFrameQueue frames;net::AccessUnitChannel channel;std::mutex mutex;std::condition_variable cv;
    bool firstCapture=false;std::exception_ptr failure;std::atomic<bool> abort{false};std::atomic<uint64_t> initializing{0},ready{0};
    auto fail=[&](std::exception_ptr e){
        {std::lock_guard<std::mutex> lock(mutex);if(!failure)failure=e;}abort=true;frames.fail(e);
        try{channel.fail(e);}catch(...){}cv.notify_all();
    };
    auto warmRgb=rr::draw({}, {},0,rr::Status::NoInput);vv::OwnedFrame warm;warm.nv12=rr::yuv420sp(warmRgb.rgb,rr::width,rr::height,false);warm.generatedNs=ns();warm.inferenceResult=false;
    proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
    vv::EncodeResult encoded{};uint64_t auCount=0;std::thread network,encoder;std::unique_ptr<app::Engine> engine;
    try{
        network=std::thread([&]{try{net::serveOwnedAccessUnits(channel,{},out/"network");}catch(...){fail(std::current_exception());}});
        encoder=std::thread([&]{try{
            auto latest=std::make_shared<const vv::OwnedFrame>(warm);uint64_t previous=0;bool previousReal=false;unsigned packetId=0;net::AccessUnitAssembler assembler;
            auto produce=[&](unsigned id,uint64_t sampled)->std::optional<vv::ResidentSample>{
                frames.check();check(!abort,"Global stop before video sample");const auto begin=initializing.load(),initialized=ready.load();
                if(begin&&!initialized){const auto now=ns();check(now>=begin&&now-begin<60000000000ULL,"Engine initialization exceeds60s");}
                if(initialized&&sampled>=initialized&&sampled-initialized>=20000000000ULL){frames.stop();return {};}
                if(auto frame=frames.popLatest())latest=std::move(frame);
                sampled=ns();auto frame=*latest;frame.encodedId=id;frame.repeatedSource=frame.inferenceResult&&previousReal&&frame.invocation==previous;
                previous=frame.invocation;previousReal=frame.inferenceResult;proof::markEncodedFrame(frame.nv12,id);
                samples<<"{\"encoded_id\":"<<id<<",\"sample_ns\":"<<sampled<<",\"source_frame_id\":"<<frame.sourceFrame<<",\"invocation\":"<<frame.invocation<<",\"generated_ns\":"<<frame.generatedNs
                    <<",\"inference_result\":"<<(frame.inferenceResult?"true":"false")<<",\"repeated_source\":"<<(frame.repeatedSource?"true":"false")<<"}"<<std::endl;
                return vv::ResidentSample{std::move(frame),sampled};
            };
            auto capture=[&](vv::OwnedPacket packet){
                packets<<"{\"packet\":"<<packetId++<<",\"pts_us\":"<<packet.ptsUs<<",\"bytes\":"<<packet.bytes.size()<<",\"flags\":"<<packet.flags<<"}"<<std::endl;
                if(auto unit=assembler.consume(packet.bytes,packet.ptsUs)){
                    auLog<<"{\"encoded_id\":"<<unit->id<<",\"pts_us\":"<<unit->ptsUs<<",\"idr\":"<<(unit->idr?"true":"false")<<",\"slice_bytes\":"<<unit->slice.size()<<"}"<<std::endl;
                    channel.publish(std::move(*unit));
                }
            };
            vv::ResidentOptions cfg;cfg.allowVpuStream=true;
            encoded=vv::encodeResident(out/"encoder",cfg,produce,capture,[&]{std::lock_guard<std::mutex> lock(mutex);firstCapture=true;cv.notify_all();});
            auCount=assembler.pictures();channel.close();
        }catch(...){fail(std::current_exception());}});
        {std::unique_lock<std::mutex> lock(mutex);check(cv.wait_for(lock,std::chrono::seconds(6),[&]{return firstCapture||abort.load();}),"First VPU capture timeout");if(failure)std::rethrow_exception(failure);}
        app::Config cfg;cfg.graph=package/"graph/piw24_ZG.json";cfg.raw=package/"graph/piw24_ZG.raw";cfg.evidence=out/"engine";cfg.allow_device_init=true;cfg.minimal_log=true;cfg.diagnostic_frames=4;
        initializing=ns();engine=std::make_unique<app::Engine>(cfg);check(ns()-initializing<60000000000ULL,"Engine init exceeded60s");ready=ns();
        lifecycle<<std::setprecision(17)<<"{\"event\":\"Engine_created\",\"time_ns\":"<<ready<<",\"init_ms\":"<<engine->init_ms()<<"}"<<std::endl;
        pose::input::TcpWindowInput input(out/"tcp-input");
        for(size_t i=0;i<cases.size();++i){
            frames.check();check(!abort,"Global stop before inference");
            auto actual=input.next();
            check(actual.frame_id==cases[i].window.frame_id&&actual.source_time_ns==cases[i].window.source_time_ns,
                  "Received CSI identity differs from diagnostic oracle");
            check(std::memcmp(actual.csi.data(),cases[i].window.csi.data(),sizeof(actual.csi))==0,
                  "Received CSI payload differs from diagnostic oracle");
            auto result=engine->process_window(actual);proof::saveVerifiedResult(cases[i],result,i,out,calls);
            auto rgb=rr::draw(result.scores,result.poses,result.frame_id);for(const auto& point:rgb.projected)check(point[1]<590,"Joint overlaps diagnostic marker");
            vv::OwnedFrame frame;frame.nv12=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);frame.sourceFrame=result.frame_id;frame.invocation=result.invocation;frame.generatedNs=ns();
            proof::persistBytes(out/"frames"/("result"+std::to_string(i)+".nv12"),frame.nv12.data(),frame.nv12.size());frames.publish(std::move(frame));
        }
        input.finish(cases.size());
        engine->save_evidence(); // Engine stays alive while encoding repeats/drains.
    }catch(...){fail(std::current_exception());if(engine)try{engine->save_evidence();}catch(...){}}
    if(encoder.joinable())encoder.join();
    if(network.joinable())network.join();
    lifecycle<<"{\"event\":\"workers_joined\",\"time_ns\":"<<ns()<<"}"<<std::endl;
    engine.reset();lifecycle<<"{\"event\":\"Engine_destroyed\",\"time_ns\":"<<ns()<<"}"<<std::endl;
    const auto stats=frames.stats();auto queueLog=trace(out/"queue-stats.json");queueLog<<"{\"published\":"<<stats.published<<",\"overwritten\":"<<stats.overwritten<<",\"coalesced\":"<<stats.coalesced<<",\"consumed\":"<<stats.consumed<<",\"high_water\":"<<stats.highWater<<",\"AU_high_water\":"<<channel.highWater()<<"}\n";
    if(failure)std::rethrow_exception(failure);
    check(stats.published==cases.size()&&stats.consumed==cases.size()&&stats.overwritten==0&&stats.coalesced==0,"Fixed2Hz picture lost");
    check(auCount==encoded.submitted&&encoded.submitted<1000,"Capture/AU/sample coverage differs");
    auto summary=trace(out/"summary.json");summary<<"{\"stage\":\""<<mode<<"\",\"forward_calls\":"<<cases.size()<<",\"encoded_frames\":"<<encoded.submitted<<",\"access_units\":"<<auCount<<",\"Engine_alive_until_workers_joined\":true,\"RTSP\":true,\"HDMI\":false,\"sdk_profiling\":false}\n";return 0;
}
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
