#include "producer_sdk.hpp"
#include "producer_schedule.hpp"
#include "scratch_vpu_load.hpp"
#include "vpu_ioctl_observation.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
namespace {uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}}
int main(int argc,char**argv){
    using namespace pose::producer;namespace fs=std::filesystem;using Clock=std::chrono::steady_clock;
    fs::path out;std::unique_ptr<SdkGroup> sdk;std::unique_ptr<pose::scratch::VpuLoad> video;std::unique_ptr<pose::video_observation::Observer> observer;
    std::exception_ptr failure;unsigned completed=0;std::ofstream lifecycle;
    try{
        need(argc==7,"MODE GRAPH RAW PATTERNS FRESH-OUTPUT --allow-device-init required");
        const std::string mode=argv[1];need(mode=="off"||mode=="on","Unknown video mode");need(std::string(argv[6])=="--allow-device-init","Explicit hardware mode required");
        out=argv[5];need(!fs::exists(out),"Preserve prior evidence");fs::create_directory(out);lifecycle.open(out/"lifecycle.jsonl");need(bool(lifecycle),"Lifecycle open failed");
        auto state=[&](const char* e){lifecycle<<"{\"event\":\""<<e<<"\",\"time_ns\":"<<now()<<"}\n";lifecycle.flush();need(bool(lifecycle),"Lifecycle save failed");};
        const auto started=Clock::now();std::array<Payload,2> payload{load(fs::path(argv[4])/"pattern-0"),load(fs::path(argv[4])/"pattern-1")};
        if(mode=="on"){
            observer=std::make_unique<pose::video_observation::Observer>();video=std::make_unique<pose::scratch::VpuLoad>(out/"vpu");video->waitReady();observer->check();state("VPU_actual_capture");
        }
        const auto init=Clock::now();sdk=std::make_unique<SdkGroup>(argv[2],argv[3],out,false);need(Clock::now()-init<std::chrono::seconds(60),"SDK initialization exceeds60s");state("SDK_initialized");
        for(unsigned i=0;i<2;++i){const auto dir=out/("memory-pattern-"+std::to_string(i));fs::create_directory(dir);sdk->memoryRoundTrip(payload[i],dir);}
        const auto deployment=text(out/"deployment.json");const auto token=std::to_string(fingerprint(Bytes(deployment.begin(),deployment.end())))+"\n";saveText(out/"deployment.ready",token);std::cout<<"DEPLOYMENT_READY\n"<<std::flush;
        while(!fs::exists(out/"forward.allow")){
            if(video){video->check();observer->check();}need(Clock::now()-started<std::chrono::seconds(50),"Finite deployment review gate timeout");std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        need(text(out/"forward.allow")==token,"Forward gate fingerprint differs");state("fixed_sequence_started");
        const auto epoch=now();
        for(unsigned i=0;i<pose::producer_schedule::count;++i){
            const auto planned=pose::producer_schedule::due(epoch,i);
            std::this_thread::sleep_until(Clock::time_point(std::chrono::nanoseconds(planned)));
            const auto actual=now();need(pose::producer_schedule::inSlot(planned,actual),"Fixed sequence missed slot; no catch-up");
            need(actual-epoch<60000000000ULL,"Fixed sequence exceeds60s");if(video){video->check();observer->check();}
            const auto dir=out/("call-"+std::to_string(i));fs::create_directory(dir);const auto&p=payload[i%2];
            saveFile(dir/"input-486.f32",p.inputs[0]);saveFile(dir/"input-478.f16",p.inputs[1]);
            saveText(dir/"identity.json","{\"invocation\":"+std::to_string(i)+",\"pattern\":"+std::to_string(i%2)+",\"planned_ns\":"+std::to_string(planned)+",\"actual_start_ns\":"+std::to_string(actual)+",\"epoch_ns\":"+std::to_string(epoch)+",\"no_catch_up\":true}\n");
            sdk->forwardSave(p,dir,i);compareSaved(dir,p);saveText(dir/"comparison.json","{\"saved_before_compare\":true,\"FP32_values\":11760,\"bitwise_equal\":true}\n");
            ++completed;if(video){video->check();observer->check();}need(now()-actual<pose::producer_schedule::period,"Call exhausted slot; no catch-up");
        }
        state("fixed_sequence_completed");
    }catch(...){failure=std::current_exception();}
    if(video){video->requestStop(bool(failure));try{video->join();video->check();}catch(...){if(!failure){failure=std::current_exception();}}}
    if(observer){try{observer->finish(out/"vpu-ioctl.jsonl");}catch(...){if(!failure){failure=std::current_exception();}}}
    if(lifecycle){lifecycle<<"{\"event\":\"workers_joined\",\"time_ns\":"<<now()<<"}\n";lifecycle.flush();}
    sdk.reset();
    if(lifecycle){lifecycle<<"{\"event\":\"SDK_destroyed\",\"time_ns\":"<<now()<<"}\n";lifecycle.flush();}
    video.reset();observer.reset();
    try{
        if(!out.empty()&&fs::is_directory(out)){saveText(out/"summary.json","{\"completed\":"+std::to_string(completed)+",\"requested\":100,\"all_bitwise\":"+std::string(!failure&&completed==100?"true":"false")+",\"root_cause_resolved\":false}\n");}
        if(failure){std::rethrow_exception(failure);}need(completed==100,"Sequence incomplete");std::cout<<"Fixed100 A/B alternating passed; video load="<<argv[1]<<"\n";return 0;
    }catch(const std::exception&e){
        if(!out.empty()&&fs::is_directory(out)){try{saveText(out/"failure.txt",e.what());}catch(...){} }
        std::cerr<<"STOP: "<<e.what()<<'\n';return 1;
    }
}
