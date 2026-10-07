#include "application_core.hpp"
#include "lazy_runtime_validation.hpp"
#include "tcp_receiver.hpp"
#include <iostream>
#include "skeleton_render.hpp"

using namespace pose_v1::runtime_detail;
namespace app=pose_v1::application;namespace net=pose_v1::transport;
namespace rr=pose_v1::render;
struct Case {std::string name;pose_v1::Window window;pose_v1::Tokens gold;};
static std::vector<Case> catalog(const fs::path& package){
    std::vector<Case> cases;std::ifstream cat(package/"cases.tsv");need(bool(cat),"Missing case catalog");std::string row;
    while(std::getline(cat,row)){std::istringstream line(row);std::string set,name,extra;uint64_t frame,time;
        need(bool(line>>set>>name>>frame>>time)&&!(line>>extra),"Invalid catalog");if(set!="base")continue;
        need(name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe case");
        Case c;c.name=name;c.window=pose_v1::read_window((package/"inputs"/(name+".csi")).string());need(c.window.frame_id==frame&&c.window.source_time_ns==time,"Catalog identity");
        auto raw=bytes(package/"reference"/(name+".input.f32"),sizeof(c.gold));std::memcpy(c.gold.data(),raw.data(),raw.size());cases.push_back(c);
    }need(cases.size()==3,"Base case count");return cases;
}
static void raster_write(const fs::path&p,const std::vector<uint8_t>&b){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());need(bool(f),"Raster write failed");}
static void persist(const fs::path&out,const std::string&stem,const rr::Frame&f){
    std::ofstream ppm(out/(stem+".ppm"),std::ios::binary);ppm<<"P6\n1280 720\n255\n";ppm.write(reinterpret_cast<const char*>(f.rgb.data()),f.rgb.size());need(bool(ppm),"PPM write failed");
    auto begin=std::chrono::steady_clock::now();auto rgb565=rr::rgb565_le(f.rgb,rr::width,rr::height),nv12=rr::yuv420sp(f.rgb,rr::width,rr::height,false),nv21=rr::yuv420sp(f.rgb,rr::width,rr::height,true);double convert=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
    raster_write(out/(stem+".rgb565le"),rgb565);raster_write(out/(stem+".nv12"),nv12);raster_write(out/(stem+".nv21"),nv21);
    std::ofstream meta(out/(stem+".json"));meta<<std::setprecision(17)<<"{\"frame_id\":"<<f.frame_id<<",\"top_index\":"<<f.top_index<<",\"score\":"<<f.score<<",\"render_ms\":"<<f.render_ms<<",\"three_format_conversion_ms\":"<<convert<<",\"clipped_joints\":"<<f.clipped_joints<<",\"selected_raw\":[";
    for(size_t i=0;i<42;++i){if(i)meta<<',';meta<<f.selected_raw[i];}meta<<"],\"projected\":[";for(size_t i=0;i<14;++i){if(i)meta<<',';meta<<'['<<f.projected[i][0]<<','<<f.projected[i][1]<<']';}meta<<"]}\n";need(bool(meta),"Metadata write failed");
}
static void output(const fs::path& out,size_t call,const app::Result&r,std::ostream& log,uint64_t session,double queue_ms,double arrival_ms){
    auto stem="call"+std::to_string(call);auto image=rr::draw(r.scores,r.poses,r.frame_id);
    need(image.top_index==r.best_index && std::memcmp(image.selected_raw.data(),r.selected_pose.data(),sizeof(r.selected_pose))==0,"Renderer selection changed model result");
    persist(out,stem,image);write(out/(stem+".scores.f32"),std::string(reinterpret_cast<const char*>(r.scores.data()),sizeof(r.scores)));
    write(out/(stem+".poses.f32"),std::string(reinterpret_cast<const char*>(r.poses.data()),sizeof(r.poses)));pose_v1::write_tokens((out/(stem+".input.f32")).string(),r.input);
    log<<std::setprecision(17)<<"{\"call\":"<<call<<",\"frame_id\":"<<r.frame_id<<",\"source_time_ns\":"<<r.source_time_ns<<",\"invocation\":"<<r.invocation<<",\"session\":"<<session
       <<",\"frozen_reference_checked\":"<<(r.frozen_reference_checked?"true":"false")<<",\"top_index\":"<<r.best_index<<",\"before_clear\":"<<r.before_clear<<",\"before_forward\":"<<r.before_forward
       <<",\"completed_layers\":"<<r.completed_layers<<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks<<",\"process_ms\":"<<r.process_ms<<",\"preprocess_ms\":"<<r.preprocess_ms
       <<",\"forward_ms\":"<<r.forward_ms<<",\"final_wait_ms\":"<<r.final_wait_ms<<",\"queue_ms\":"<<queue_ms<<",\"arrival_to_result_ms\":"<<arrival_ms<<"}\n";log.flush();
}
static int run(int argc,char**argv){
    need(argc>=2,"Expected host-check|regression|serve");std::string mode=argv[1];need(mode=="host-check"||mode=="regression"||mode=="serve","Unknown application stage");
    std::map<std::string,std::string> f;bool device=false;
    for(int i=2;i<argc;++i){std::string k=argv[i];if(k=="--allow-device-init"){need(!device,"Duplicate hardware flag");device=true;continue;}
        need(i+1<argc && std::set<std::string>{"--output","--package","--graph","--raw","--bind","--port","--max-frames","--sessions","--idle-ms"}.count(k),"Invalid option");need(f.emplace(k,argv[++i]).second,"Duplicate option");}
    need(device==(mode!="host-check"),"Hardware scope requires explicit device flag");for(auto k:{"--output","--package","--graph"})need(f.count(k)==1,"Missing required path");
    fs::path out=f.at("--output"),package=f.at("--package");need(!fs::exists(out),"Preserve application results");fs::create_directory(out);
    write(out/"run-config.json","{\"mode\":"+quote(mode)+",\"device_init_allowed\":"+(device?"true":"false")+",\"content_capture\":"+(mode=="host-check"?"true":"false")+",\"sdk_profiling\":false}\n");
    std::unique_ptr<app::Engine> engine;
    try{
        if(mode=="host-check"){
            auto trace=file(out/"bridge.jsonl");bridge::configure(&trace,false);
            std::vector<std::string> a={"pose_application_render_check","--graph",f.at("--graph"),"--fixtures",(package/"fixtures").string(),"--output",(out/"host").string()};std::vector<char*> args;for(auto&v:a)args.push_back(v.data());
            need(mixed_host_check(int(args.size()),args.data())==0,"Host107 failed");host_content_check(xir::Network::CreateFromJsonFile(f.at("--graph")),out);write(out/"summary.json","{\"stage\":\"host-check\",\"cases\":107,\"device_opened\":false}\n");return 0;
        }
        need(f.count("--raw"),"RAW required");
        // Validate serve options before any Device::Open.
        int port=39001,idle=5000;size_t max_frames=0,sessions=1;std::string bind="192.168.126.49";
        if(mode=="serve"){
            need(f.count("--max-frames"),"Finite validation frame limit required");max_frames=std::stoul(f.at("--max-frames"));need(max_frames>0&&max_frames<=1000,"Frame limit outside1..1000");
            if(f.count("--port"))port=std::stoi(f.at("--port"));
            if(f.count("--idle-ms"))idle=std::stoi(f.at("--idle-ms"));
            if(f.count("--sessions"))sessions=std::stoul(f.at("--sessions"));
            if(f.count("--bind"))bind=f.at("--bind");
            need(port>0&&port<=65535&&idle>=100&&idle<=60000&&sessions>0&&sessions<=8,"Invalid receiver configuration");
        }
        app::Config c;c.graph=f.at("--graph");c.raw=f.at("--raw");c.evidence=out;c.allow_device_init=device;c.minimal_log=true;c.capture=false;c.diagnostic_frames=mode=="regression"?8:4;
        engine=std::make_unique<app::Engine>(c);auto log=file(out/"results.jsonl");size_t call=0;
        if(mode=="regression"){
            auto cases=catalog(package);
            for(size_t j=0;j<4;++j){auto&tc=cases[j%3];auto expected_scores=bytes(package/"r6-reference"/(tc.name+".scores.f32"),400);auto expected_poses=bytes(package/"r6-reference"/(tc.name+".poses.f32"),16800);
                for(bool checked:{true,false}){auto r=checked?engine->process_window_checked(tc.window,tc.name,tc.gold):engine->process_window(tc.window);
                    need(std::memcmp(r.scores.data(),expected_scores.data(),400)==0&&std::memcmp(r.poses.data(),expected_poses.data(),16800)==0,"Production/verification result differs fromr6");
                    need(std::memcmp(r.input.data(),tc.gold.data(),sizeof(tc.gold))==0,"Production PS input differs");need(r.frozen_reference_checked==checked,"Wrong API validation mode");output(out,call++,r,log,0,0,0);
                }
            }
        }else{
            net::Receiver rx(bind,uint16_t(port),idle,sessions);write(out/"listener.json","{\"address\":"+quote(bind)+",\"port\":"+std::to_string(rx.port())+",\"queue_capacity\":1,\"idle_ms\":"+std::to_string(idle)+"}\n");
            std::cout<<"READY "<<rx.port()<<'\n'<<std::flush;
            while(call<max_frames&&!rx.finished()){
                auto item=rx.pop(std::chrono::milliseconds(100));rx.check();if(!item)continue;auto begin=Clock::now();auto r=engine->process_window(item->window);
                auto done=Clock::now();double queue=std::chrono::duration<double,std::milli>(begin-item->arrived).count(),elapsed=std::chrono::duration<double,std::milli>(done-item->arrived).count();
                need(!r.frozen_reference_checked,"Production network path used frozen reference");output(out,call++,r,log,item->session,queue,elapsed);
            }
            rx.stop();rx.check();auto s=rx.stats();write(out/"network.json","{\"sessions\":"+std::to_string(s.sessions)+",\"received\":"+std::to_string(s.received)+",\"rejected\":"+std::to_string(s.rejected)+",\"overwritten\":"+std::to_string(s.overwritten)+",\"reconnect_discarded\":"+std::to_string(s.reconnect_discarded)+",\"consumed\":"+std::to_string(call)+"}\n");
            need(call==max_frames,"Network ended before required complete frames");need(s.rejected==0&&s.overwritten==0&&s.reconnect_discarded==0,"Fixed validation stream lost/rejected frames");
        }
        engine->save_evidence();write(out/"summary.json","{\"stage\":"+quote(mode)+",\"forward_calls\":"+std::to_string(call)+",\"sdk_profiling\":false,\"video_initialized\":false,\"diagnostic_frames_bounded\":true}\n");return 0;
    }catch(const std::exception&e){if(engine)try{engine->save_evidence();}catch(...){}write(out/"failure.json","{\"status\":\"failed_stop_no_retry\",\"error\":"+quote(e.what())+"}\n");throw;}
}
int main(int argc,char**argv){try{return run(argc,argv);}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
