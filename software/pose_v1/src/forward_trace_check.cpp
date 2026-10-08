// Finite orchestration: main-owned Engine, encoding worker, event-loop worker.
// All math, SDK completion/copies, renderer and VPU protocol remain in modules.
#include "pipeline_fixture_source.hpp"
#include "video_frame_marker.hpp"
#include "skeleton_render.hpp"
#include "resident_frame_queue.hpp"
#include "vpu_resident_encoder.hpp"
#include "online_rtsp.hpp"
#include "process_window_input.hpp"
#include "system_timing.hpp"
#include "display_process.hpp"
#include "display_queue.hpp"
#include <sstream>
#include "presaved_result_evidence.hpp"
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
    check(argc==5||argc==8,"Usage: host-check|process-three|measure-2hz|measure-5hz|trace-5hz PACKAGE FRESH-RESULTS --finite-check [--allow-device-init --allow-vpu-stream --allow-network]");
    const std::string mode=argv[1];const fs::path package=argv[2],out=argv[3];const bool host=mode=="host-check";
    check(host||mode=="process-three"||mode=="measure-2hz"||(mode=="measure-5hz"||mode=="trace-5hz"),"Unknown live mode");check(std::string(argv[4])=="--finite-check"&&!fs::exists(out),"Preserve evidence / explicit finite check");
    check((argc==8)==!host,"Hardware/network authorization differs");
    if(!host)check(std::string(argv[5])=="--allow-device-init"&&std::string(argv[6])=="--allow-vpu-stream"&&std::string(argv[7])=="--allow-network","Explicit hardware/network flags required");
    fs::create_directory(out);
    if(host){proof::validatedHostGate(package,out);auto f=trace(out/"summary.json");f<<"{\"stage\":\"host-check\",\"cases\":107,\"device_opened\":false,\"VPU_streamed\":false}\n";return 0;}
    auto cases=proof::fixtureWindows(package,mode!="process-three");if(mode!="process-three")cases.pop_back();std::vector<pose::measurement::Measurement> measured;measured.reserve(33);fs::create_directory(out/"engine");fs::create_directory(out/"frames");
    std::ostringstream samples,packets,auLog;auto lifecycle=trace(out/"lifecycle.jsonl");
    vv::ResidentFrameQueue frames;net::AccessUnitChannel channel;std::mutex mutex;std::condition_variable cv;
    namespace display=pose::display;
    display::Queue poses;
    struct DisplayRecord {uint64_t invocation,frame,request,dispatch,begin,drawn,converted,received,published;};
    std::vector<DisplayRecord> displayRecords;displayRecords.reserve(33);
    std::unique_ptr<display::Process> displayProcess;
    bool firstCapture=false;std::exception_ptr failure;std::atomic<bool> abort{false};std::atomic<uint64_t> initializing{0},ready{0};
    auto fail=[&](std::exception_ptr e){
        {std::lock_guard<std::mutex> lock(mutex);if(!failure)failure=e;}abort=true;frames.fail(e);poses.fail(e);
        try{channel.fail(e);}catch(...){}cv.notify_all();
    };
    auto warmRgb=rr::draw({}, {},0,rr::Status::NoInput);vv::OwnedFrame warm;warm.nv12=rr::yuv420sp(warmRgb.rgb,rr::width,rr::height,false);warm.generatedNs=ns();warm.inferenceResult=false;
    // Warmup image is created before the measurement epoch.
    vv::EncodeResult encoded{};uint64_t auCount=0;std::thread network,encoder,displayPump;std::unique_ptr<app::Engine> engine;
    try{
        // exec before VPU/NPU creation; child owns no SDK or device state.
        displayProcess=std::make_unique<display::Process>(fs::canonical(argv[0]).parent_path()/"pose_display_worker",out/"display");
        displayPump=std::thread([&]{try{
            while(auto pose=poses.next()){
                const auto dispatch=ns();auto image=displayProcess->render(*pose,[&]{return abort.load();});
                vv::OwnedFrame frame;frame.nv12=std::move(image.nv12);frame.sourceFrame=image.frame;frame.invocation=image.invocation;frame.generatedNs=image.convertEnd;
                frames.publish(std::move(frame));
                displayRecords.push_back({image.invocation,image.frame,pose->publishedNs,dispatch,image.renderBegin,image.drawEnd,image.convertEnd,image.receivedEnd,ns()});
            }
            displayProcess->finish();
        }catch(...){fail(std::current_exception());}});
        network=std::thread([&]{try{net::serveOwnedAccessUnits(channel,{},out/"network");}catch(...){fail(std::current_exception());}});
        encoder=std::thread([&]{try{
            auto latest=std::make_shared<const vv::OwnedFrame>(warm);uint64_t previous=0;bool previousReal=false;unsigned packetId=0;net::AccessUnitAssembler assembler;
            auto produce=[&](unsigned id,uint64_t sampled)->std::optional<vv::ResidentSample>{
                frames.check();check(!abort,"Global stop before video sample");const auto begin=initializing.load(),initialized=ready.load();
                if(begin&&!initialized){const auto now=ns();check(now>=begin&&now-begin<60000000000ULL,"Engine initialization exceeds60s");}
                if(initialized&&sampled>=initialized&&sampled-initialized>=20000000000ULL){frames.stop();return {};}
                const auto adopt=ns();if(auto frame=frames.popLatest())latest=std::move(frame);
                sampled=ns();auto frame=*latest;frame.encodedId=id;frame.repeatedSource=frame.inferenceResult&&previousReal&&frame.invocation==previous;
                previous=frame.invocation;previousReal=frame.inferenceResult;proof::markEncodedFrame(frame.nv12,id);
                samples<<"{\"encoded_id\":"<<id<<",\"sample_ns\":"<<sampled<<",\"source_frame_id\":"<<frame.sourceFrame<<",\"invocation\":"<<frame.invocation<<",\"adopt_ns\":"<<adopt<<",\"generated_ns\":"<<frame.generatedNs
                    <<",\"inference_result\":"<<(frame.inferenceResult?"true":"false")<<",\"repeated_source\":"<<(frame.repeatedSource?"true":"false")<<"}"<<'\n';
                return vv::ResidentSample{std::move(frame),sampled};
            };
            auto capture=[&](vv::OwnedPacket packet){
                packets<<"{\"packet\":"<<packetId++<<",\"pts_us\":"<<packet.ptsUs<<",\"capture_ns\":"<<ns()<<",\"bytes\":"<<packet.bytes.size()<<",\"flags\":"<<packet.flags<<"}"<<'\n';
                if(auto unit=assembler.consume(packet.bytes,packet.ptsUs)){
                    auLog<<"{\"encoded_id\":"<<unit->id<<",\"pts_us\":"<<unit->ptsUs<<",\"idr\":"<<(unit->idr?"true":"false")<<",\"slice_bytes\":"<<unit->slice.size()<<"}"<<'\n';
                    channel.publish(std::move(*unit));
                }
            };
            vv::ResidentOptions cfg;cfg.allowVpuStream=true;
            encoded=vv::encodeResident(out/"encoder",cfg,produce,capture,[&]{std::lock_guard<std::mutex> lock(mutex);firstCapture=true;cv.notify_all();});
            auCount=assembler.pictures();channel.close();
        }catch(...){fail(std::current_exception());}});
        {std::unique_lock<std::mutex> lock(mutex);check(cv.wait_for(lock,std::chrono::seconds(6),[&]{return firstCapture||abort.load();}),"First VPU capture timeout");if(failure)std::rethrow_exception(failure);}
        app::Config cfg;cfg.graph=package/"graph/piw24_ZG.json";cfg.raw=package/"graph/piw24_ZG.raw";cfg.evidence=out/"engine";cfg.allow_device_init=true;cfg.minimal_log=true;cfg.diagnostic_frames=mode=="trace-5hz"?32:0;
        initializing=ns();engine=std::make_unique<app::Engine>(cfg);check(ns()-initializing<60000000000ULL,"Engine init exceeded60s");ready=ns();
        lifecycle<<std::setprecision(17)<<"{\"event\":\"Engine_created\",\"time_ns\":"<<ready<<",\"init_ms\":"<<engine->init_ms()<<"}"<<std::endl;
        pose::measurement::TimedWindowInput input;
        while(auto item=input.next()){
            frames.check();check(!abort,"Global stop before timing inference");
            check(measured.size()<pose::measurement::sentLimit,"Timing owned results capacity exceeded");
            check(item->sequence==item->window.frame_id-pose::measurement::transportBase,"Transport sequence differs");
            pose::measurement::Measurement record;record.item=std::move(*item);record.dequeued=ns();
            const auto& fixture=pose::measurement::fixtureFor(cases,record.item.window.frame_id);
            check(record.item.window.source_time_ns==fixture.window.source_time_ns&&std::memcmp(record.item.window.csi.data(),fixture.window.csi.data(),sizeof(record.item.window.csi))==0,"Timing raw payload differs");
            record.processBegin=ns();record.result=engine->process_window(record.item.window);record.processEnd=ns();
            // Preserve the complete returned value even if the unchanged gate fails.
            measured.push_back(std::move(record));auto& v=measured.back();
            pose::measurement::verify(fixture,v.result,v.item.window,measured.size()-1);v.verifyEnd=ns();
            display::Pose pose;pose.frame=v.result.frame_id;pose.invocation=v.result.invocation;pose.scores=v.result.scores;pose.poses=v.result.poses;pose.publishedNs=ns();poses.publish(std::move(pose));
        }
        input.finish(out,!(mode=="measure-5hz"||mode=="trace-5hz"),mode=="process-three"?4:33);
        poses.close();

    }catch(...){fail(std::current_exception());if(engine)try{engine->save_evidence();}catch(...){}}
    if(displayPump.joinable())displayPump.join();
    if(encoder.joinable())encoder.join();
    if(network.joinable())network.join();
    lifecycle<<"{\"event\":\"workers_joined\",\"time_ns\":"<<ns()<<"}"<<std::endl;
    auto displayLog=trace(out/"display-timing.jsonl");
    for(const auto& d:displayRecords){
        check(d.invocation<measured.size()&&measured[d.invocation].result.frame_id==d.frame,"Display timing ownership differs");
        auto& v=measured[d.invocation];v.drawEnd=d.drawn;v.convertEnd=d.converted;v.published=d.published;
        displayLog<<"{\"invocation\":"<<d.invocation<<",\"frame_id\":"<<d.frame<<",\"request_ns\":"<<d.request<<",\"dispatch_ns\":"<<d.dispatch<<",\"render_begin_ns\":"<<d.begin<<",\"draw_end_ns\":"<<d.drawn<<",\"convert_end_ns\":"<<d.converted<<",\"receive_end_ns\":"<<d.received<<",\"published_ns\":"<<d.published<<"}\n";
    }
    const auto displayStats=poses.stats();auto qlog=trace(out/"display-queue.json");
    qlog<<"{\"published\":"<<displayStats.published<<",\"adopted\":"<<displayStats.adopted<<",\"overwritten\":"<<displayStats.overwritten<<",\"coalesced\":"<<displayStats.coalesced<<",\"high_water\":"<<displayStats.highWater<<",\"IPC_inflight_limit\":1}\n";
    displayProcess.reset();
    // All large diagnostic writes happen after workers complete, outside the measurement.
    try{
        pose::measurement::save(measured,cases,out);if(engine)engine->save_evidence();
        proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
        for(size_t i=0;i<measured.size();++i){const auto& r=measured[i].result;auto rgb=rr::draw(r.scores,r.poses,r.frame_id);auto pixels=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);proof::persistBytes(out/"frames"/("result"+std::to_string(i)+".nv12"),pixels.data(),pixels.size());}
    }catch(...){if(!failure)failure=std::current_exception();}
    for(auto pair:{std::make_pair("samples.jsonl",samples.str()),std::make_pair("packets.jsonl",packets.str()),std::make_pair("access-units.jsonl",auLog.str())}){auto f=trace(out/pair.first);f<<pair.second;}
    engine.reset();lifecycle<<"{\"event\":\"Engine_destroyed\",\"time_ns\":"<<ns()<<"}"<<std::endl;
    const auto stats=frames.stats();auto queueLog=trace(out/"queue-stats.json");queueLog<<"{\"published\":"<<stats.published<<",\"overwritten\":"<<stats.overwritten<<",\"coalesced\":"<<stats.coalesced<<",\"consumed\":"<<stats.consumed<<",\"high_water\":"<<stats.highWater<<",\"AU_high_water\":"<<channel.highWater()<<"}\n";
    if(failure)std::rethrow_exception(failure);
    check(stats.published==measured.size()&&((mode=="measure-5hz"||mode=="trace-5hz")||(stats.consumed==measured.size()&&stats.overwritten==0&&stats.coalesced==0)),"Fixed2Hz picture lost");
    check(displayStats.published==measured.size()&&displayStats.adopted==measured.size()&&displayStats.overwritten==0&&displayStats.coalesced==0,"Display result coverage differs");
    check(auCount==encoded.submitted&&encoded.submitted<1000,"Capture/AU/sample coverage differs");
    auto summary=trace(out/"summary.json");summary<<"{\"stage\":\""<<mode<<"\",\"forward_calls\":"<<measured.size()<<",\"encoded_frames\":"<<encoded.submitted<<",\"access_units\":"<<auCount<<",\"Engine_alive_until_workers_joined\":true,\"RTSP\":true,\"HDMI\":false,\"sdk_profiling\":false}\n";return 0;
}
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
