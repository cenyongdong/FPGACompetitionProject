#include "scratch_copy_sdk.hpp"
#include "scratch_vpu_load.hpp"
#include "invocation_evidence.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
#include <stdexcept>
namespace {void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}}
int main(int argc,char**argv){try{namespace s=pose::scratch;namespace fs=std::filesystem;using Clock=std::chrono::steady_clock;
    need(argc==4||argc==5,"scratch memory|vpu FRESH-OUTPUT --allow-device-init [--allow-vpu-stream]");std::string mode=argv[1];fs::path out=argv[2];const bool vpu=mode=="vpu";
    need((vpu||mode=="memory")&&!fs::exists(out)&&std::string(argv[3])=="--allow-device-init"&&(vpu?argc==5&&std::string(argv[4])=="--allow-vpu-stream":argc==4),"Scratch explicit mode/authorization differs");fs::create_directory(out);
    std::unique_ptr<s::SdkScratch> sdk;std::unique_ptr<s::VpuLoad> video;std::exception_ptr failure;std::vector<s::Pair> selected;selected.reserve(2);s::Pair current;bool hasCurrent=false;unsigned completed=0;std::ofstream trace(out/"pairs.jsonl"),lifecycle(out/"lifecycle.jsonl");
    try{if(vpu){video=std::make_unique<s::VpuLoad>(out/"vpu");video->waitReady();lifecycle<<"{\"event\":\"VPU_actual_capture\",\"time_ns\":"<<now()<<"}\n";}
        auto initialize=Clock::now();sdk=std::make_unique<s::SdkScratch>(out/"sdk");need(Clock::now()-initialize<std::chrono::seconds(60),"Scratch device init exceeds60s");lifecycle<<"{\"event\":\"SDK_opened\",\"time_ns\":"<<now()<<"}\n";
        current=sdk->readSources();hasCurrent=true;s::savePair(current,out/"preload");need(s::matches(current),"Scratch initial SDK data mismatch");hasCurrent=false;
        const auto epoch=Clock::now();
        for(size_t i=0;i<s::pairLimit;++i){if(vpu){video->check();std::this_thread::sleep_until(epoch+std::chrono::milliseconds(200*i));video->check();}
            need(Clock::now()-epoch<std::chrono::seconds(vpu?20:30),"Scratch bounded copy duration exceeded");current=sdk->copyPair();hasCurrent=true;const bool same=s::matches(current);
            trace<<"{\"pair\":"<<i<<",\"matched\":"<<(same?"true":"false")<<",\"fnv_a\":"<<s::fingerprint(current.values[0])<<",\"fnv_b\":"<<s::fingerprint(current.values[1])<<",\"copy_a_begin_ns\":"<<current.copyBegin[0]<<",\"copy_a_end_ns\":"<<current.copyEnd[0]<<",\"shadow_a_begin_ns\":"<<current.shadowBegin[0]<<",\"shadow_a_end_ns\":"<<current.shadowEnd[0]<<",\"copy_b_begin_ns\":"<<current.copyBegin[1]<<",\"copy_b_end_ns\":"<<current.copyEnd[1]<<",\"shadow_b_begin_ns\":"<<current.shadowBegin[1]<<",\"shadow_b_end_ns\":"<<current.shadowEnd[1]<<"}\n";trace.flush();need(bool(trace),"Scratch trace save failed");
            need(same,"Scratch consecutive copy mismatch");++completed;if(i==0||i+1==s::pairLimit)selected.push_back(current);hasCurrent=false;
        }need(Clock::now()-epoch<std::chrono::seconds(vpu?20:30),"Scratch final duration exceeded");
    }catch(...){failure=std::current_exception();}
    if(video)video->requestStop(bool(failure));
    if(failure&&hasCurrent){try{s::savePair(current,out/"failed-pair");}catch(...){}if(sdk)for(unsigned round=0;round<2;++round)try{s::savePair(sdk->readSources(),out/("late-source"+std::to_string(round)));}catch(const std::exception&e){std::ofstream(out/("late-source"+std::to_string(round)+".error.txt"))<<e.what();}}
    if(video){try{video->join();video->check();}catch(...){if(!failure)failure=std::current_exception();}}
    lifecycle<<"{\"event\":\"workers_joined\",\"time_ns\":"<<now()<<"}\n";
    pose::invocation_evidence::flush({{"first-last-owned",[&]{for(size_t i=0;i<selected.size();++i)s::savePair(selected[i],out/(i?"last-pair":"first-pair"));}},
        {"summary",[&]{std::ofstream f(out/"summary.json");f<<"{\"mode\":\""<<mode<<"\",\"completed_pairs\":"<<completed<<",\"full_model_Session\":false,\"NPU_forward\":false,\"all_bitwise\":"<<(!failure&&completed==100?"true":"false")<<",\"pacing_between_pairs_ms\":"<<(vpu?200:0)<<",\"pacing_inside_pair\":false,\"zero_copy\":false}\n";f.close();need(bool(f),"Scratch summary save failed");}}
    },failure,out/"persistence-ledger.json");sdk.reset();lifecycle<<"{\"event\":\"SDK_destroyed\",\"time_ns\":"<<now()<<"}\n";video.reset();if(failure)std::rethrow_exception(failure);std::cout<<"Scratch100 pairs passed; no model/NPU forward; VPU="<<vpu<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
