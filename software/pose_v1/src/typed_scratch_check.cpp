#include "typed_scratch_sdk.hpp"
#include "scratch_vpu_load.hpp"
#include "invocation_evidence.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>
#include <stdexcept>
namespace {
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
}
int main(int argc,char**argv){try{
    namespace ts=pose::typed_scratch;namespace s=pose::scratch;namespace fs=std::filesystem;using Clock=std::chrono::steady_clock;
    need(argc==5||argc==6,"typed static|dynamic|vpu GRAPH FRESH-OUTPUT --allow-device-init [--allow-vpu-stream]");
    const std::string mode=argv[1];const bool vpu=mode=="vpu",dynamic=mode!="static";const fs::path graph=argv[2],out=argv[3];
    need((mode=="static"||mode=="dynamic"||vpu)&&fs::is_regular_file(graph)&&!fs::exists(out)&&std::string(argv[4])=="--allow-device-init"&&(vpu?argc==6&&std::string(argv[5])=="--allow-vpu-stream":argc==5),"Typed mode/authorization differs");
    fs::create_directory(out);std::unique_ptr<ts::SdkScratch> sdk;std::unique_ptr<s::VpuLoad> video;std::exception_ptr failure;
    std::vector<ts::Pair> selected;selected.reserve(2);ts::Pair current;ts::Writes writes;bool hasCurrent=false;size_t attempt=0,patternIndex=0;unsigned completed=0,normalReadPairs=0;std::string phase="setup";
    std::ofstream trace(out/"pairs.jsonl"),lifecycle(out/"lifecycle.jsonl");
    try{
        if(vpu){video=std::make_unique<s::VpuLoad>(out/"vpu");video->waitReady();lifecycle<<"{\"event\":\"VPU_actual_capture\",\"time_ns\":"<<now()<<"}\n";}
        const auto initialize=Clock::now();sdk=std::make_unique<ts::SdkScratch>(graph,out/"sdk");need(Clock::now()-initialize<std::chrono::seconds(60),"Typed SDK init exceeds60s");
        lifecycle<<"{\"event\":\"SDK_opened\",\"time_ns\":"<<now()<<"}\n";phase="initial_write";sdk->writePattern(0,writes);hasCurrent=true;phase="preload";++normalReadPairs;sdk->readSources(current);s::savePair(current,out/"preload");need(ts::matches(current,0),"Typed initial read mismatch");hasCurrent=false;
        const auto epoch=Clock::now();
        for(size_t i=0;i<s::pairLimit;++i){
            attempt=i;patternIndex=dynamic?i+1:0;current=ts::Pair{};writes=ts::Writes{};hasCurrent=true;phase="between_pairs";
            if(vpu){video->check();std::this_thread::sleep_until(epoch+std::chrono::milliseconds(200*i));video->check();}
            need(Clock::now()-epoch<std::chrono::seconds(vpu?20:30),"Typed copy duration exceeded");
            if(dynamic){phase="update";sdk->writePattern(patternIndex,writes);}
            phase="copy";sdk->copyPair(current);const bool same=ts::matches(current,patternIndex);
            trace<<"{\"pair\":"<<i<<",\"pattern_index\":"<<patternIndex<<",\"previous_pattern_index\":"<<(patternIndex?patternIndex-1:0)<<",\"matched\":"<<(same?"true":"false")<<",\"fnv_a\":"<<s::fingerprint(current.values[0])<<",\"fnv_b\":"<<s::fingerprint(current.values[1])<<",\"write_a_begin_ns\":"<<writes.begin[0]<<",\"write_a_end_ns\":"<<writes.end[0]<<",\"write_b_begin_ns\":"<<writes.begin[1]<<",\"write_b_end_ns\":"<<writes.end[1]<<",\"copy_a_begin_ns\":"<<current.copyBegin[0]<<",\"copy_a_end_ns\":"<<current.copyEnd[0]<<",\"shadow_a_begin_ns\":"<<current.shadowBegin[0]<<",\"shadow_a_end_ns\":"<<current.shadowEnd[0]<<",\"copy_b_begin_ns\":"<<current.copyBegin[1]<<",\"copy_b_end_ns\":"<<current.copyEnd[1]<<",\"shadow_b_begin_ns\":"<<current.shadowBegin[1]<<",\"shadow_b_end_ns\":"<<current.shadowEnd[1]<<"}\n";trace.flush();need(bool(trace),"Typed pair trace failed");
            need(same,"Typed consecutive copy mismatch");++completed;if(i==0||i+1==s::pairLimit){selected.push_back(current);}hasCurrent=false;
        }
        need(Clock::now()-epoch<std::chrono::seconds(vpu?20:30),"Typed final duration exceeded");
    }catch(...){failure=std::current_exception();}
    if(video){video->requestStop(bool(failure));}
    bool failureCaptured=false;
    const auto captureFailure=[&]{
        failureCaptured=true;
        pose::invocation_evidence::flush({
            {"original-owned",[&]{if(hasCurrent||!current.values[0].empty()){s::saveAvailable(current,out/"failed-pair");}}},
            {"current-expected",[&]{ts::saveExpected(patternIndex,out/"expected-current");}},
            {"previous-expected",[&]{ts::saveExpected(patternIndex?patternIndex-1:0,out/"expected-previous");}},
            {"attempt-identity",[&]{std::ofstream f(out/"failed-attempt.json");f<<"{\"attempt\":"<<attempt<<",\"pattern_index\":"<<patternIndex<<",\"phase\":\""<<phase<<"\",\"write_a_begin_ns\":"<<writes.begin[0]<<",\"write_a_end_ns\":"<<writes.end[0]<<",\"write_b_begin_ns\":"<<writes.begin[1]<<",\"write_b_end_ns\":"<<writes.end[1]<<",\"original_error_preserved\":true}\n";f.close();need(bool(f),"Typed failure identity save failed");}}
        },failure,out/"failure-persistence-ledger.json");
        if(sdk){for(unsigned round=0;round<2;++round){ts::Pair late;try{sdk->readSources(late);s::savePair(late,out/("late-source"+std::to_string(round)));}catch(const std::exception&e){try{s::saveAvailable(late,out/("late-source"+std::to_string(round)+"-partial"));}catch(...){}std::ofstream(out/("late-source"+std::to_string(round)+".error.txt"))<<e.what();}}}
    };
    if(failure){captureFailure();}
    if(video){if(!failure){phase="encoder_drain";}try{video->join();video->check();}catch(...){if(!failure){failure=std::current_exception();}}}
    if(failure&&!failureCaptured){captureFailure();}
    lifecycle<<"{\"event\":\"workers_joined\",\"time_ns\":"<<now()<<"}\n";
    pose::invocation_evidence::flush({
        {"first-last-owned",[&]{for(size_t i=0;i<selected.size();++i){s::savePair(selected[i],out/(i?"last-pair":"first-pair"));}}},
        {"summary",[&]{std::ofstream f(out/"summary.json");f<<"{\"mode\":\""<<mode<<"\",\"completed_pairs\":"<<completed<<",\"all_bitwise\":"<<(!failure&&completed==100?"true":"false")<<",\"actual_model_types\":true,\"dynamic_writes\":"<<(dynamic?"true":"false")<<",\"full_model_Session\":false,\"NPU_forward\":false,\"normal_source_read_pairs\":"<<normalReadPairs<<",\"pacing_between_pairs_ms\":"<<(vpu?200:0)<<",\"pacing_inside_pair\":false,\"zero_copy\":false}\n";f.close();need(bool(f),"Typed summary save failed");}}
    },failure,out/"persistence-ledger.json");
    sdk.reset();lifecycle<<"{\"event\":\"SDK_destroyed\",\"time_ns\":"<<now()<<"}\n";video.reset();
    if(failure){std::rethrow_exception(failure);}
    std::cout<<"Typed scratch100 pairs passed; no model/NPU forward; mode="<<mode<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
