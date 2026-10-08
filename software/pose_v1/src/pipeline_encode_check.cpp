#include "application_core.hpp"
#include "lazy_runtime_validation.hpp"
#include "skeleton_render.hpp"
#include "vpu_pipeline_encoder.hpp"
#include <iostream>

using namespace pose_v1::runtime_detail;
namespace app=pose_v1::application;namespace rr=pose_v1::render;namespace vv=pose::video;
namespace { // Local helper types must not collide with frozen Host fixture Case.
struct Case {std::string name;pose_v1::Window window;pose_v1::Tokens gold;std::vector<char> scores,poses;};
static std::vector<Case> catalog(const fs::path& package) {
    std::ifstream cat(package/"cases.tsv");need(bool(cat),"Case catalog missing");std::vector<Case> cases;std::string row;
    while(std::getline(cat,row)) {
        std::istringstream line(row);std::string set,name,extra;uint64_t frame,time;
        need(bool(line>>set>>name>>frame>>time)&&!(line>>extra),"Invalid catalog");if(set!="base")continue;
        need(name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe case name");
        Case c;c.name=name;c.window=pose_v1::read_window((package/"inputs"/(name+".csi")).string());
        need(c.window.frame_id==frame&&c.window.source_time_ns==time,"Case identity differs");
        auto input=bytes(package/"reference"/(name+".input.f32"),sizeof(c.gold));std::memcpy(c.gold.data(),input.data(),input.size());
        c.scores=bytes(package/"r6-reference"/(name+".scores.f32"),400);c.poses=bytes(package/"r6-reference"/(name+".poses.f32"),16800);
        cases.push_back(std::move(c));
    }
    need(cases.size()==3,"Three base cases required");return cases;
}
static void persist(const fs::path& path,const void* data,size_t size) {
    std::ofstream f(path,std::ios::binary);f.write(static_cast<const char*>(data),size);need(bool(f),"Output write failed");
}
static void compare(const app::Result& r,const Case& c) {
    need(r.frame_id==c.window.frame_id && r.source_time_ns==c.window.source_time_ns,"Runtime source differs");
    need(std::memcmp(r.input.data(),c.gold.data(),sizeof(c.gold))==0,"PS input differs");
    need(std::memcmp(r.scores.data(),c.scores.data(),400)==0 && std::memcmp(r.poses.data(),c.poses.data(),16800)==0,"Full runtime output differs fromr6");
    need(r.before_forward==0 && r.completed_layers==745 && r.host_callbacks==7 && r.zg_callbacks==7,"Frame completion/callback baseline differs");
}
static void record(const fs::path& dest,const std::string& stem,const app::Result& r,const Case& c,std::ostream& log) {
    persist(dest/(stem+".input.f32"),r.input.data(),sizeof(r.input));persist(dest/(stem+".scores.f32"),r.scores.data(),sizeof(r.scores));persist(dest/(stem+".poses.f32"),r.poses.data(),sizeof(r.poses));
    log<<std::setprecision(17)<<"{\"stem\":"<<quote(stem)<<",\"case\":"<<quote(c.name)<<",\"frame_id\":"<<r.frame_id
       <<",\"invocation\":"<<r.invocation<<",\"before_clear\":"<<r.before_clear<<",\"before_forward\":"<<r.before_forward
       <<",\"completed_layers\":"<<r.completed_layers<<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks
       <<",\"checked_reference\":"<<(r.frozen_reference_checked?"true":"false")<<",\"process_ms\":"<<r.process_ms<<"}"<<std::endl;
}
static uint64_t stamp() {return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
static void mark(std::vector<uint8_t>& image,unsigned encodedId) {
    auto yrect=[&](int x0,int y0,int x1,int y1,uint8_t color){for(int y=y0;y<y1;++y)std::fill(image.begin()+size_t(y)*1280+x0,image.begin()+size_t(y)*1280+x1,color);};
    yrect(40,600,1240,680,16);
    for(int y=300;y<340;++y)std::fill(image.begin()+1280*720+size_t(y)*1280+40,image.begin()+1280*720+size_t(y)*1280+1240,128);
    for(unsigned bit=0;bit<6;++bit)yrect(40+bit*64,600,88+bit*64,632,encodedId&(1<<bit)?235:16);
    yrect(40+encodedId*21,640,64+encodedId*21,680,235);
}
static void contracts(const fs::path& out) {
    vv::OwnedFrame valid;valid.nv12.resize(vv::nv12FrameBytes,16);valid.generatedNs=1;vv::validateOwnedFrame(valid,0);
    unsigned rejected=0;
    auto rejects=[&](vv::OwnedFrame f,unsigned id){bool failed=false;try{vv::validateOwnedFrame(f,id);}catch(const std::exception&){failed=true;}need(failed,"Malformed frame accepted");++rejected;};
    auto f=valid;f.nv12.pop_back();rejects(f,0);f=valid;f.nv12.push_back(0);rejects(f,0);
    f=valid;f.encodedId=1;rejects(f,0);f=valid;f.generatedNs=0;rejects(f,0);rejects(valid,60);
    // Missing callback is rejected before any /dev/video0 open/output creation.
    vv::EncodeOptions options;options.allowVpuStream=true;bool failed=false;
    try{vv::encodeNv12Producer(out/"must-not-exist",options,{},{});}catch(const std::exception&){failed=true;}
    need(failed&&!fs::exists(out/"must-not-exist"),"Missing callback reached device/output path");
    // Moved packets own independent bytes even after original capture storage changes.
    std::vector<uint8_t> driver{0,0,0,1,0x67,1,2};vv::OwnedPacket packet;packet.bytes.assign(driver.begin(),driver.end());
    vv::OwnedPacket kept;vv::PacketConsumer consumer=[&](vv::OwnedPacket p){kept=std::move(p);};consumer(std::move(packet));
    std::fill(driver.begin(),driver.end(),0);need(kept.bytes==std::vector<uint8_t>({0,0,0,1,0x67,1,2}),"Packet borrows capture storage");
    write(out/"contracts.json","{\"status\":\"passed\",\"frame_rejections\":"+std::to_string(rejected)+",\"missing_callbacks_rejected_before_device\":true,\"packet_owned_after_capture_reuse\":true}\n");
}
static int run(int argc,char** argv) {
    need(argc==5 || argc==7,"Usage: host-check|combined PACKAGE FRESH-RESULTS --finite-check [--allow-device-init --allow-vpu-stream]");
    const std::string mode=argv[1];need(mode=="host-check"||mode=="combined","Invalid mode");
    need(!std::string(argv[2]).empty()&&!std::string(argv[3]).empty(),"Package/output path required");
    // Positional paths intentionally avoid shell option ambiguity.
    const fs::path package=argv[2],out=argv[3];
    need(std::string(argv[4])=="--finite-check","Explicit finite diagnostic flag required");
    const bool device=argc==7;
    need(device==(mode=="combined"),"Hardware scope requires explicit flags");
    if(device)need(std::string(argv[5])=="--allow-device-init"&&std::string(argv[6])=="--allow-vpu-stream","Hardware flags differ");
    need(!fs::exists(out),"Preserve results");fs::create_directory(out);
    auto cases=catalog(package);contracts(out);
    if(mode=="host-check") {
        auto trace=file(out/"bridge.jsonl");bridge::configure(&trace,false);
        std::vector<std::string> args={"pipeline_encode_check","--graph",(package/"graph/piw24_ZG.json").string(),"--fixtures",(package/"fixtures").string(),"--output",(out/"host").string()};
        std::vector<char*> a;for(auto& arg:args)a.push_back(arg.data());need(mixed_host_check(a.size(),a.data())==0,"Host107 failed");
        write(out/"summary.json","{\"stage\":\"host-check\",\"cases\":107,\"device_opened\":false,\"VPU_streamed\":false}\n");return 0;
    }
    std::unique_ptr<app::Engine> engine;
    try {
        fs::create_directory(out/"engine");app::Config config;
        config.graph=package/"graph/piw24_ZG.json";config.raw=package/"graph/piw24_ZG.raw";config.evidence=out/"engine";
        config.allow_device_init=true;config.minimal_log=true;config.diagnostic_frames=8;
        auto results=file(out/"inference.jsonl");
        fs::create_directory(out/"frames");auto frameLog=file(out/"frames.jsonl");auto packets=file(out/"packets.jsonl");
        auto lifecycle=file(out/"lifecycle.jsonl");
        vv::OwnedFrame cached;unsigned packetCount=0;size_t packetBytes=0;bool warmCapture=false;
        auto producer=[&](unsigned id) {
            need(id<10,"Unexpected producer request");
            if(id<2) {
                if(id==0) {
                    auto f=rr::draw({}, {},0,rr::Status::NoInput);
                    std::ofstream ppm(out/"frames/warmup.ppm",std::ios::binary);ppm<<"P6\n1280 720\n255\n";ppm.write(reinterpret_cast<const char*>(f.rgb.data()),f.rgb.size());need(bool(ppm),"Warmup PPM write failed");
                    cached.nv12=rr::yuv420sp(f.rgb,rr::width,rr::height,false);cached.generatedNs=stamp();cached.inferenceResult=false;
                }
                auto frame=cached;frame.encodedId=id;frame.repeatedSource=bool(id%2);mark(frame.nv12,id);return frame;
            }
            if(!engine) {
                need(warmCapture,"VPU output must be observed before loading model");
                lifecycle<<"{\"event\":\"VPU_capture_before_Engine\",\"time_ns\":"<<stamp()<<",\"packet_count\":"<<packetCount<<"}"<<std::endl;
                engine=std::make_unique<app::Engine>(config);
                lifecycle<<"{\"event\":\"Engine_created\",\"time_ns\":"<<stamp()<<",\"init_ms\":"<<engine->init_ms()<<"}"<<std::endl;
                for(unsigned i=0;i<4;++i) {const auto& c=cases[i%3];auto r=engine->process_window_checked(c.window,c.name,c.gold);compare(r,c);record(out,"regression"+std::to_string(i),r,c,results);}
            }
            const auto source=(id-2)/2;
            if(id%2==0) {
                const auto& c=cases[source%3];auto r=engine->process_window(c.window);compare(r,c);need(!r.frozen_reference_checked,"Production used frozen reference");
                record(out,"production"+std::to_string(source),r,c,results);
                auto f=rr::draw(r.scores,r.poses,r.frame_id);
                for(const auto& point:f.projected)need(point[1]<590,"Joint touches diagnostic overlay");
                std::ofstream ppm(out/"frames"/("source"+std::to_string(source)+".ppm"),std::ios::binary);ppm<<"P6\n1280 720\n255\n";ppm.write(reinterpret_cast<const char*>(f.rgb.data()),f.rgb.size());need(bool(ppm),"PPM write failed");
                cached.nv12=rr::yuv420sp(f.rgb,rr::width,rr::height,false);cached.sourceFrame=r.frame_id;cached.invocation=r.invocation;cached.generatedNs=stamp();cached.inferenceResult=true;
                frameLog<<std::setprecision(17)<<"{\"source_index\":"<<source<<",\"case\":"<<quote(c.name)<<",\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation
                        <<",\"render_ms\":"<<f.render_ms<<",\"top_index\":"<<f.top_index<<",\"projected\":[";
                for(size_t j=0;j<14;++j){if(j)frameLog<<',';frameLog<<'['<<f.projected[j][0]<<','<<f.projected[j][1]<<']';}frameLog<<"]}"<<std::endl;
            }
            auto frame=cached;frame.encodedId=id;frame.repeatedSource=bool(id%2);mark(frame.nv12,id);return frame;
        };
        vv::PacketConsumer consumer=[&](vv::OwnedPacket p) {
            need(p.bytes.size()<=2*1024*1024,"Packet exceeds negotiated bound");
            if(!p.bytes.empty()&&!engine)warmCapture=true;
            persist(out/("packet"+std::to_string(packetCount)+".h264"),p.bytes.data(),p.bytes.size());
            packets<<"{\"packet\":"<<packetCount<<",\"pts_us\":"<<p.ptsUs<<",\"flags\":"<<p.flags<<",\"bytes\":"<<p.bytes.size()<<"}"<<std::endl;
            ++packetCount;packetBytes+=p.bytes.size();need(packetCount<=32 && packetBytes<=16*1024*1024,"Packet diagnostic capacity");
        };
        vv::EncodeOptions options;options.frameCount=10;options.allowVpuStream=true;
        const auto encoded=vv::encodeNv12Producer(out/"encoder",options,producer,consumer,2);
        need(engine&&encoded.submitted==10&&encoded.returned==10&&encoded.drained&&encoded.encodedBytes==packetBytes,"Combined encoding incomplete");
        engine->save_evidence();write(out/"summary.json","{\"stage\":\"combined\",\"regression_forward_calls\":4,\"production_forward_calls\":4,\"encoded_frames\":10,\"warmup_frames\":2,\"device_opened\":true,\"VPU_streamed\":true,\"RTSP_initialized\":false,\"HDMI_initialized\":false,\"realtime_throughput_verified\":false}\n");return 0;
    }catch(...) {if(engine)try{engine->save_evidence();}catch(...){}throw;}
}
}
int main(int argc,char** argv) {try{return run(argc,argv);}catch(const std::exception& e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
