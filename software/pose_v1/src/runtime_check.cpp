#include "runtime_core.hpp"
#include "runtime_validation.hpp"
#include <cctype>

using namespace pose_v1::runtime_detail;
namespace rt=pose_v1::runtime;
struct Case { std::string name;pose_v1::Window window;pose_v1::Tokens gold; };
static uint64_t rss_kib() {
    std::ifstream f("/proc/self/status");std::string s;
    while(std::getline(f,s))if(s.rfind("VmRSS:",0)==0){std::istringstream row(s.substr(6));uint64_t n;row>>n;need(bool(row),"Cannot parse RSS");return n;}
    need(false,"No Linux RSS status");return 0;
}
static int run(int argc,char** argv) {
    need(argc>=2,"Expected host-check|e0|n1|p1");std::string phase=argv[1];
    need(phase=="host-check" || phase=="e0" || phase=="n1" || phase=="p1","Unknown stage");
    std::map<std::string,std::string> flags;bool hardware=false;
    for(int i=2;i<argc;++i) {
        std::string flag=argv[i];if(flag=="--allow-device-init"){need(!hardware,"Duplicate hardware flag");hardware=true;continue;}
        need(i+1<argc && std::set<std::string>{"--graph","--raw","--package","--output"}.count(flag),"Unknown/missing option");
        need(flags.emplace(flag,argv[++i]).second,"Duplicate option");
    }
    need(hardware==(phase!="host-check"),"Hardware scope requires explicit flag");
    need(flags.count("--output") && flags.count("--graph") && flags.count("--package"),"Missing paths");
    fs::path output=flags.at("--output"),package=flags.at("--package");
    need(!fs::exists(output),"Preserve previous results");fs::create_directory(output);
    auto stages=file(output/"stages.jsonl");auto mark=[&](const char* s){stages<<"{\"stage\":"<<quote(s)<<"}\n";stages.flush();};
    auto config=file(output/"run-config.json");config<<"{\"mode\":"<<quote(phase)<<",\"device_init_allowed\":"<<(hardware?"true":"false")
        <<",\"content_capture\":"<<(phase!="p1"?"true":"false")<<",\"sdk_profiling\":true,\"frame_state_reset_level\":"<<(hardware?"1":"null")
        <<",\"sdk_wait_ms\":10000,\"minimal_log\":"<<(phase=="p1"?"true":"false")<<"}\n";config.close();
    std::unique_ptr<rt::Engine> engine;
    try {
        mark("started");
        if(phase=="host-check") {
            auto trace=file(output/"bridge.jsonl");bridge::configure(&trace,false);
            std::vector<std::string> values={"pose_mixed_check","--graph",flags.at("--graph"),"--fixtures",(package/"fixtures").string(),"--output",(output/"host").string()};
            std::vector<char*> ptr;for(auto& v:values)ptr.push_back(v.data());
            need(mixed_host_check(int(ptr.size()),ptr.data())==0,"Host107 regression failed");mark("host_bridge_regression_completed");
            host_content_check(xir::Network::CreateFromJsonFile(flags.at("--graph")),output);mark("host_content_paths_completed");return 0;
        }
        need(flags.count("--raw"),"RAW required");
        std::vector<Case> cases;std::ifstream cat(package/"cases.tsv");need(bool(cat),"Missing catalog");std::string row;
        while(std::getline(cat,row)) {
            std::istringstream line(row);std::string set,name,extra;uint64_t frame,time;
            need(bool(line>>set>>name>>frame>>time) && !(line>>extra),"Invalid catalog row");
            need(!name.empty() && name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe case name");
            if(set!=(phase=="n1"?"expanded":"base"))continue;
            Case c;c.name=name;c.window=pose_v1::read_window((package/"inputs"/(name+".csi")).string());
            need(c.window.frame_id==frame && c.window.source_time_ns==time,"CSI header differs from catalog");
            auto gold=bytes(package/"reference"/(name+".input.f32"),sizeof(c.gold));std::memcpy(c.gold.data(),gold.data(),gold.size());cases.push_back(c);
        }
        need(cases.size()==(phase=="n1"?27U:3U),"Case count differs");
        // Preload the reviewed r6 proof before initialization or measurement.
        std::vector<std::pair<std::string,std::string>> r6;
        if(phase=="p1")for(const auto& c:cases) {
            const auto scores=bytes(package/"r6-reference"/(c.name+".scores.f32"),400);
            const auto poses=bytes(package/"r6-reference"/(c.name+".poses.f32"),16800);
            r6.emplace_back(std::string(scores.begin(),scores.end()),std::string(poses.begin(),poses.end()));
        }
        rt::Config c;c.graph=flags.at("--graph");c.raw=flags.at("--raw");c.evidence=output;c.allow_device_init=hardware;c.capture=phase!="p1";c.minimal_log=phase=="p1";
        engine=std::make_unique<rt::Engine>(c);mark("original_to_effective_bindings_validated");
        const size_t calls=phase=="p1"?33:cases.size()+1;
        std::vector<rt::Result> all;std::vector<uint64_t> rss;all.reserve(calls);rss.reserve(calls);
        for(size_t call=0;call<calls;++call) {
            size_t i=phase=="p1"?call%3:(call==cases.size()?0:call);
            mark("forward_started");auto result=engine->process_window(cases[i].window,cases[i].name,cases[i].gold);
            // Full correctness proof kept in RAM outside the measured interval.
            if(phase=="p1") {
                need(result.scores==r6[i].first && result.poses==r6[i].second,"Performance path differs from frozen r6; stop before further calls");
                if(call==2)mark("warmup_three_r6_verified_before_measurement");
            }
            if(phase=="p1" && call>=3)need(result.scores==all[i].scores && result.poses==all[i].poses,"Benchmark response differs from first same-case result");
            if(phase!="p1" && call==cases.size())need(result.scores==all[0].scores && result.poses==all[0].poses,"Same-Session first repeat differs");
            all.push_back(std::move(result));rss.push_back(rss_kib());mark("case_completed");
        }
        engine->save_evidence();
        // Batch evidence IO is intentionally outside process_window timing.
        auto results=file(output/"results.jsonl");std::set<std::string> signatures;
        for(size_t call=0;call<calls;++call) {
            const auto& r=all[call];size_t i=phase=="p1"?call%3:(call==cases.size()?0:call);const auto& name=cases[i].name;
            std::string stem="call"+std::to_string(call);
            write(output/(stem+".scores.f32"),r.scores);write(output/(stem+".poses.f32"),r.poses);
            if(call<cases.size() && phase!="p1")signatures.insert(r.scores+r.poses);
            if(call<cases.size())pose_v1::write_tokens((output/(name+".input.f32")).string(),r.input);
            results<<"{\"case\":"<<quote(name)<<",\"frame_id\":"<<r.frame_id<<",\"source_time_ns\":"<<r.source_time_ns
                <<",\"invocation\":"<<r.invocation<<",\"output_stem\":"<<quote(stem)<<",\"top_index\":"<<r.best_index
                <<",\"before_clear\":"<<r.before_clear<<",\"before_forward\":"<<r.before_forward<<",\"completed_layers\":"<<r.completed_layers
                <<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks
                <<",\"preprocess_ms\":"<<r.preprocess_ms<<",\"prepare_ms\":"<<r.prepare_ms<<",\"state_clear_ms\":"<<r.state_clear_ms
                <<",\"forward_ms\":"<<r.forward_ms<<",\"final_wait_ms\":"<<r.final_wait_ms<<",\"output_ms\":"<<r.output_ms
                <<",\"selection_ms\":"<<r.selection_ms<<",\"process_ms\":"<<r.process_ms<<",\"cpu_ms\":"<<r.cpu_ms
                <<",\"rss_kib\":"<<rss[call]<<",\"measured\":"<<(phase=="p1" && call>=3?"true":"false")<<"}\n";
        }
        if(phase!="p1")need(signatures.size()>1,"All distinct inputs produced the same output");
        auto summary=file(output/"summary.json");summary<<"{\"stage\":"<<quote(phase)<<",\"forward_calls\":"<<calls
            <<",\"case_count\":"<<cases.size()<<",\"session_init_ms\":"<<engine->init_ms()
            <<",\"sdk_profiling\":true,\"numerical_accepted\":false,\"full_system_performance_accepted\":false}\n";
        mark("stage_completed");return 0;
    } catch(const std::exception& error) {
        if(engine)try{engine->save_evidence();}catch(...){}
        write(output/"failure.json","{\"error\":"+quote(error.what())+",\"status\":\"failed_stop_no_retry\"}\n");mark("failed_stop_no_retry");throw;
    }
}
int main(int argc,char** argv){try{return run(argc,argv);}catch(const std::exception& e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
