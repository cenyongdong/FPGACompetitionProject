#include "application_core.hpp"
#include "lazy_runtime_validation.hpp"
#include "skeleton_render.hpp"
#include "resident_frame_queue.hpp"
#include "vpu_resident_encoder.hpp"
#include <atomic>
#include <condition_variable>
#include <thread>
#include <iostream>

namespace {
using namespace pose_v1::runtime_detail;
namespace app=pose_v1::application;namespace rr=pose_v1::render;namespace vv=pose::video;
uint64_t ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
void persist(const fs::path& p,const void* data,size_t n){std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),n);need(bool(f),"Evidence write failed");}
void queueContracts(const fs::path& out){
    auto frame=[](uint64_t id){vv::OwnedFrame f;f.nv12.resize(vv::nv12FrameBytes,uint8_t(id));f.generatedNs=id;f.invocation=id;return f;};
    vv::ResidentFrameQueue q;q.publish(frame(1));q.publish(frame(2));q.publish(frame(3));
    auto two=q.pop(),three=q.pop();need(two&&three&&two->invocation==2&&three->invocation==3&&!q.pop(),"Capacity2 order/overwrite failed");
    auto s=q.stats();need(s.published==3&&s.overwritten==1&&s.consumed==2&&s.highWater==2,"Queue stats failed");
    need(two->nv12.front()==2&&three->nv12.front()==3,"Owned bytes differ");q.stop();
    bool stopped=false;try{q.publish(frame(4));}catch(const std::exception&){stopped=true;}need(stopped,"Publish after stop accepted");
    vv::ResidentFrameQueue failed;failed.fail(std::make_exception_ptr(std::runtime_error("synthetic")));
    unsigned rejected=0;for(unsigned i=0;i<3;++i){try{if(i==0)failed.pop();else if(i==1)failed.check();else failed.publish(frame(5));}catch(const std::exception&){++rejected;}}
    need(rejected==3,"Failure propagation failed");
    auto held=three;auto copy=*held;copy.nv12[0]=0;need(held->nv12[0]==3,"Repeat sample modified cached frame");
    vv::ResidentFrameQueue latest;latest.publish(frame(6));latest.publish(frame(7));
    need(latest.popLatest()->invocation==7&&!latest.popLatest()&&latest.stats().coalesced==1,"Sampler did not choose latest completed frame");
    write(out/"queue-contracts.json","{\"status\":\"passed\",\"capacity\":2,\"overwrite_oldest\":true,\"immutable_repeat\":true,\"stop_rejected\":true,\"failure_paths\":3}\n");
}
struct ResidentCase{std::string name;pose_v1::Window window;pose_v1::Tokens input;std::vector<char> scores,poses;};
std::vector<ResidentCase> catalog(const fs::path& package,const std::string& group){
    std::ifstream f(package/"cases.tsv");need(bool(f),"Catalog missing");std::vector<ResidentCase> cases;std::string row;
    while(std::getline(f,row)){
        std::istringstream r(row);std::string set,name,extra;uint64_t frame,time;
        need(bool(r>>set>>name>>frame>>time)&&!(r>>extra),"Invalid catalog row");if(set!=group)continue;
        need(name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe case name");
        ResidentCase c;c.name=name;c.window=pose_v1::read_window((package/"inputs"/(name+".csi")).string());
        need(c.window.frame_id==frame&&c.window.source_time_ns==time,"Catalog identity differs");
        auto input=bytes(package/"reference"/(name+".input.f32"),sizeof(c.input));std::memcpy(c.input.data(),input.data(),input.size());
        c.scores=bytes(package/"r6-reference"/(name+".scores.f32"),400);c.poses=bytes(package/"r6-reference"/(name+".poses.f32"),16800);cases.push_back(std::move(c));
    }
    need(cases.size()==(group=="base"?3:27),"Catalog coverage differs");return cases;
}
void mark(std::vector<uint8_t>& image,unsigned id){
    // Ten bits cover the bounded1000-frame stream, below all known joints.
    for(unsigned y=600;y<680;++y)std::fill(image.begin()+y*1280+40,image.begin()+y*1280+1240,16);
    for(unsigned y=300;y<340;++y)std::fill(image.begin()+1280*720+y*1280+40,image.begin()+1280*720+y*1280+1240,128);
    for(unsigned bit=0;bit<10;++bit)for(unsigned y=604;y<632;++y)
        std::fill(image.begin()+y*1280+44+bit*64,image.begin()+y*1280+84+bit*64,id&(1u<<bit)?235:16);
}
std::string frameHash(const std::vector<uint8_t>& bytes){
    uint64_t hash=14695981039346656037ULL;for(auto byte:bytes){hash^=byte;hash*=1099511628211ULL;}
    std::ostringstream out;out<<std::hex<<std::setw(16)<<std::setfill('0')<<hash;return out.str();
}
int run(int argc,char**argv){
    need(argc==5||argc==7,"Usage: host-check|resident-three|resident-27 PACKAGE FRESH-RESULTS --finite-check [--allow-device-init --allow-vpu-stream]");
    const std::string mode=argv[1];need(mode=="host-check"||mode=="resident-three"||mode=="resident-27","Unknown resident mode");
    const fs::path package=argv[2],out=argv[3];need(std::string(argv[4])=="--finite-check"&&!fs::exists(out),"Preserve evidence / explicit finite flag");
    need((argc==7)==(mode!="host-check"),"Hardware authorization differs");
    if(argc==7)need(std::string(argv[5])=="--allow-device-init"&&std::string(argv[6])=="--allow-vpu-stream","Hardware flags differ");
    fs::create_directory(out);queueContracts(out);
    if(mode=="host-check"){
        auto trace=file(out/"bridge.jsonl");bridge::configure(&trace,false);
        std::vector<std::string> args={"resident","--graph",(package/"graph/piw24_ZG.json").string(),"--fixtures",(package/"fixtures").string(),"--output",(out/"host").string()};
        std::vector<char*> a;for(auto& arg:args)a.push_back(arg.data());need(mixed_host_check(a.size(),a.data())==0,"Host107 failed");
        write(out/"summary.json","{\"stage\":\"host-check\",\"cases\":107,\"device_opened\":false,\"VPU_streamed\":false}\n");return 0;
    }
    auto cases=catalog(package,mode=="resident-three"?"base":"expanded");cases.push_back(cases.front());
    fs::create_directory(out/"engine");fs::create_directory(out/"frames");
    auto inference=file(out/"inference.jsonl"),samples=file(out/"samples.jsonl"),packetLog=file(out/"packets.jsonl"),lifecycle=file(out/"lifecycle.jsonl");
    vv::ResidentFrameQueue queue;std::mutex startMutex;std::condition_variable startCv;
    bool captureSeen=false;std::atomic<bool> abort{false};std::atomic<uint64_t> initBegin{0},ready{0};
    auto fail=[&](std::exception_ptr e){queue.fail(e);abort=true;startCv.notify_all();};
    auto warmRgb=rr::draw({}, {},0,rr::Status::NoInput);vv::OwnedFrame warm;
    warm.nv12=rr::yuv420sp(warmRgb.rgb,rr::width,rr::height,false);warm.generatedNs=ns();warm.inferenceResult=false;
    persist(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
    std::thread inferenceThread([&]{
        std::unique_ptr<app::Engine> engine;
        try{
            {std::unique_lock<std::mutex> lock(startMutex);need(startCv.wait_for(lock,std::chrono::seconds(6),[&]{return captureSeen||abort.load();}),"No VPU startup notification");queue.check();}
            app::Config cfg;cfg.graph=package/"graph/piw24_ZG.json";cfg.raw=package/"graph/piw24_ZG.raw";cfg.evidence=out/"engine";
            cfg.allow_device_init=true;cfg.minimal_log=true;cfg.diagnostic_frames=4;initBegin=ns();
            engine=std::make_unique<app::Engine>(cfg);need(ns()-initBegin<60000000000ULL,"Engine initialization exceeds60s");
            ready=ns();lifecycle<<"{\"event\":\"Engine_created\",\"time_ns\":"<<ready<<",\"init_ms\":"<<engine->init_ms()<<"}"<<std::endl;
            const auto first=Clock::now();
            for(size_t i=0;i<cases.size();++i){
                std::this_thread::sleep_until(first+std::chrono::milliseconds(i*500));queue.check();need(!abort,"Global stop before inference");
                const auto& c=cases[i];auto result=engine->process_window(c.window);
                need(!result.frozen_reference_checked&&std::memcmp(result.input.data(),c.input.data(),sizeof(c.input))==0,"Production input/reference mode differs");
                need(std::memcmp(result.scores.data(),c.scores.data(),400)==0&&std::memcmp(result.poses.data(),c.poses.data(),16800)==0,"Production output differs");
                need(result.before_forward==0&&result.completed_layers==745&&result.host_callbacks==7&&result.zg_callbacks==7,"Frame protocol differs");
                auto stem="result"+std::to_string(i);persist(out/(stem+".input.f32"),result.input.data(),sizeof(result.input));persist(out/(stem+".scores.f32"),result.scores.data(),400);persist(out/(stem+".poses.f32"),result.poses.data(),16800);
                auto rgb=rr::draw(result.scores,result.poses,result.frame_id);for(const auto& point:rgb.projected)need(point[1]<590,"Joint intersects marker");
                vv::OwnedFrame frame;frame.nv12=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);frame.sourceFrame=result.frame_id;frame.invocation=result.invocation;frame.generatedNs=ns();
                persist(out/"frames"/(stem+".nv12"),frame.nv12.data(),frame.nv12.size());queue.publish(std::move(frame));
                inference<<std::setprecision(17)<<"{\"call\":"<<i<<",\"case\":"<<quote(c.name)<<",\"frame_id\":"<<result.frame_id<<",\"invocation\":"<<result.invocation<<",\"completed_layers\":745,\"before_forward\":0,\"zg_callbacks\":7,\"host_callbacks\":7,\"best_index\":"<<result.best_index<<",\"process_ms\":"<<result.process_ms<<"}"<<std::endl;
            }
            engine->save_evidence();
        }catch(...){if(engine)try{engine->save_evidence();}catch(...){}fail(std::current_exception());}
    });
    vv::EncodeResult encoded{};
    std::thread encodingThread([&]{
        try{
            auto latest=std::make_shared<const vv::OwnedFrame>(warm);uint64_t previous=0;bool previousReal=false;unsigned packets=0;
            vv::ResidentOptions cfg;cfg.allowVpuStream=true;
            auto producer=[&](unsigned id,uint64_t sampled)->std::optional<vv::ResidentSample>{
                queue.check();need(!abort,"Global stop before sample");
                auto initialized=ready.load(),begin=initBegin.load();
                if(begin&&!initialized)need(sampled-begin<60000000000ULL,"Engine not ready within60s");
                if(initialized&&sampled-initialized>=20000000000ULL){queue.stop();return {};}
                if(auto next=queue.popLatest())latest=std::move(next);
                sampled=ns(); // Source selection precedes this actual sampling instant.
                auto frame=*latest;frame.encodedId=id;frame.repeatedSource=frame.inferenceResult&&previousReal&&frame.invocation==previous;
                previous=frame.invocation;previousReal=frame.inferenceResult;mark(frame.nv12,id);
                samples<<"{\"encoded_id\":"<<id<<",\"sample_ns\":"<<sampled<<",\"source_frame_id\":"<<frame.sourceFrame<<",\"invocation\":"<<frame.invocation<<",\"generated_ns\":"<<frame.generatedNs<<",\"inference_result\":"<<(frame.inferenceResult?"true":"false")<<",\"repeated_source\":"<<(frame.repeatedSource?"true":"false")<<",\"marked_NV12_fnv1a64\":"<<quote(frameHash(frame.nv12))<<"}"<<std::endl;
                return vv::ResidentSample{std::move(frame),sampled};
            };
            auto capture=[&](vv::OwnedPacket packet){packetLog<<"{\"packet\":"<<packets++<<",\"pts_us\":"<<packet.ptsUs<<",\"bytes\":"<<packet.bytes.size()<<",\"flags\":"<<packet.flags<<"}"<<std::endl;};
            encoded=vv::encodeResident(out/"encoder",cfg,producer,capture,[&]{std::lock_guard<std::mutex> lock(startMutex);captureSeen=true;startCv.notify_one();});
        }catch(...){fail(std::current_exception());}
    });
    encodingThread.join();inferenceThread.join();
    const auto stats=queue.stats();
    write(out/"queue-stats.json","{\"published\":"+std::to_string(stats.published)+",\"overwritten\":"+std::to_string(stats.overwritten)
        +",\"coalesced\":"+std::to_string(stats.coalesced)+",\"consumed\":"+std::to_string(stats.consumed)+",\"high_water\":"+std::to_string(stats.highWater)+"}\n");
    queue.check();
    need(stats.published==cases.size()&&stats.overwritten==0&&stats.coalesced==0&&stats.consumed==cases.size(),"Fixed2Hz source lost in frame queue");
    write(out/"summary.json","{\"stage\":"+quote(mode)+",\"forward_calls\":"+std::to_string(cases.size())+",\"encoded_frames\":"+std::to_string(encoded.submitted)+",\"queue_capacity\":2,\"published\":"+std::to_string(stats.published)+",\"overwritten\":"+std::to_string(stats.overwritten)+",\"consumed\":"+std::to_string(stats.consumed)+",\"queue_high_water\":"+std::to_string(stats.highWater)+",\"contexts_opened\":1,\"sdk_profiling\":false,\"HDMI\":false,\"RTSP\":false}\n");
    return 0;
}
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
