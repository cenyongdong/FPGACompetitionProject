#include "demo_video.hpp"
#include "demo_results.hpp"
#include "tcp_receiver.hpp"
#include "demo_engine.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <map>

namespace {
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void need(bool v,const char* m){if(!v)throw std::runtime_error(m);}
}
int main(int argc,char** argv) {
    namespace fs=std::filesystem;
    fs::path out;std::unique_ptr<pose::display::Process> display;std::unique_ptr<wifi_demo::Video> video;
    std::unique_ptr<wifi_demo::Engine> engine;std::unique_ptr<pose_v1::transport::Receiver> input;
    std::ofstream lifecycle;wifi_demo::Results results;std::exception_ptr failure;uint64_t received=0,overwritten=0;
    try {
        std::map<std::string,std::string> options;
        for(int i=1;i<argc;++i) {
            std::string name=argv[i];need(!options.count(name),"Duplicate demo option");
            if(name=="--allow-device-init"||name=="--allow-vpu-stream"||name=="--allow-network")options[name]="yes";
            else {need(i+1<argc,"Missing demo option value");options[name]=argv[++i];}
        }
        for(const auto& p:options)need(p.first=="--model-dir"||p.first=="--output"||p.first=="--bind"||p.first=="--input-port"||p.first=="--rtsp-port"||p.first=="--max-frames"||p.first=="--allow-device-init"||p.first=="--allow-vpu-stream"||p.first=="--allow-network","Unknown demo option");
        need(options.count("--model-dir")&&options.count("--output")&&options.count("--allow-device-init")&&options.count("--allow-vpu-stream")&&options.count("--allow-network"),"Model/output and three explicit hardware flags required");
        auto get=[&](const char* n,const char* d){return options.count(n)?options.at(n):std::string(d);};
        auto number=[&](const char* n,const char* d){auto s=get(n,d);need(!s.empty()&&s.find_first_not_of("0123456789")==std::string::npos,"Invalid unsigned demo option");return std::stoul(s);};
        const auto maximum=number("--max-frames","60"),port=number("--input-port","39001"),rtsp=number("--rtsp-port","8554");
        need(maximum>=1&&maximum<=100&&port>=1024&&port<=65535&&rtsp>=1024&&rtsp<=65535&&port!=rtsp,"Demo option bounds differ");
        out=options.at("--output");need(!fs::exists(out)&&fs::create_directory(out),"Fresh demo output directory required");
        lifecycle.open(out/"lifecycle.jsonl");auto state=[&](const char* e){lifecycle<<"{\"event\":\""<<e<<"\",\"board_ns\":"<<now()<<"}\n";lifecycle.flush();need(bool(lifecycle),"Lifecycle write failed");};
        const auto began=now();
        display=std::make_unique<pose::display::Process>(fs::canonical(argv[0]).parent_path()/"pose_display_worker",out/"display");
        video=std::make_unique<wifi_demo::Video>(*display,out/"video",unsigned(rtsp));video->waitCapture();state("VPU_actual_capture");
        video->beginInitialization();engine=std::make_unique<wifi_demo::Engine>(options.at("--model-dir"),out/"engine");video->initialized();state("Engine_created_main_thread");
        input=std::make_unique<pose_v1::transport::Receiver>(get("--bind","192.168.126.49"),uint16_t(port),5000,1);
        {std::ofstream f(out/"input.ready");f<<port<<'\n';need(bool(f),"Input ready write failed");}
        std::cout<<"DEMO_INPUT_READY "<<port<<" RTSP rtsp://192.168.126.49:"<<rtsp<<"/pose\n"<<std::flush;
        const auto ready=now();
        while(results.size()<maximum) {
            video->check();input->check();need(!input->stats().rejected,"CSI record rejected");need(now()-began<170000000000ULL,"Demo total budget exceeded");
            auto item=input->pop(std::chrono::milliseconds(100));
            if(!item) {if(input->finished())break;need(results.size()||now()-ready<60000000000ULL,"Demo input startup timeout");continue;}
            const auto arrived=std::chrono::duration_cast<std::chrono::nanoseconds>(item->arrived.time_since_epoch()).count();
            auto r=engine->process_window(item->window);const auto returned=now();
            pose::display::Pose p;p.frame=r.frame_id;p.invocation=r.invocation;p.scores=r.scores;p.poses=r.poses;p.publishedNs=returned;
            results.add(std::move(item->window),std::move(r),uint64_t(arrived),returned);video->publish(std::move(p));
        }
        input->stop();input->check();const auto counters=input->stats();received=counters.received;overwritten=counters.overwritten;
        need(!counters.rejected&&results.size()>0,"No valid completed demo frames");state("production_stopped");
    } catch(...) {failure=std::current_exception();if(input)input->stop();if(video)video->abort(failure);}
    if(video) {try {video->finish();}catch(...) {if(!failure)failure=std::current_exception();}}
    input.reset();video.reset();display.reset();
    if(lifecycle){lifecycle<<"{\"event\":\"workers_joined\",\"board_ns\":"<<now()<<"}\n";lifecycle.flush();}
    if(!out.empty()&&fs::is_directory(out)) {
        auto attempt=[&](auto f){try {f();}catch(...) {if(!failure)failure=std::current_exception();}};
        attempt([&]{results.save(out/"results");});
        attempt([&]{if(engine)engine->save_evidence();});
    }
    engine.reset();
    if(lifecycle){lifecycle<<"{\"event\":\"Engine_destroyed\",\"board_ns\":"<<now()<<"}\n";lifecycle.flush();}
    try {
        if(!out.empty()&&fs::is_directory(out)) {std::ofstream f(out/"summary.json");f<<"{\"completed\":"<<results.size()<<",\"received\":"<<received<<",\"overwritten\":"<<overwritten<<",\"workers_joined_before_Engine_destroyed\":true,\"RTSP\":true,\"HDMI\":false,\"failed\":"<<(failure?"true":"false")<<"}\n";need(bool(f),"Summary save failed");}
        if(failure)std::rethrow_exception(failure);
        std::cout<<"Demo completed "<<results.size()<<" real CSI windows\n";return 0;
    } catch(const std::exception& e) {if(!out.empty()&&fs::is_directory(out)){std::ofstream f(out/"failure.txt");f<<e.what()<<'\n';}std::cerr<<"DEMO_STOP: "<<e.what()<<'\n';return 1;}
}
