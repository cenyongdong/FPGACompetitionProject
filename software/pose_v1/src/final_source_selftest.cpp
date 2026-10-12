#include "final_source_recorder.hpp"
#include "owned_result_save.hpp"
#include <cstring>
#include <iostream>
#include <limits>
#include <thread>
namespace {
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
std::vector<char> read(const std::filesystem::path&p){std::ifstream f(p,std::ios::binary);return {std::istreambuf_iterator<char>(f),{}};}
}
int main(int argc,char**argv){try{
    need(argc==2,"Fresh test directory required");std::filesystem::path root=argv[1];need(!std::filesystem::exists(root),"Preserve test directory");std::filesystem::create_directory(root);
    using pose::final_source::Recorder;Recorder recorder;recorder.begin(100000,0);std::vector<char> b(16800,42);unsigned reads=0,refused=0;
    auto reject=[&](auto fn){try{fn();}catch(const std::exception&){++refused;return;}throw std::runtime_error("Expected refusal absent");};
    recorder.source(582,0,"{}",b,[&](char*p,size_t n){++reads;std::memset(p,17,n);});b[0]=99;recorder.output(437,0,std::vector<char>(400,7));
    reject([&]{recorder.source(582,0,"{}",b,[](char*,size_t){});});reject([&]{recorder.source(188,0,"{}",b,[](char*,size_t){});});reject([&]{recorder.output(582,0,std::vector<char>(4));});
    bool threadRefused=false;std::thread t([&]{try{recorder.begin(100001,1);}catch(const std::exception&){threadRefused=true;}});t.join();need(threadRefused,"Foreign thread accepted");
    recorder.capture(root/"complete","original finite mismatch");need(reads==2&&read(root/"complete/host.582.0.f32")[0]==42&&read(root/"complete/round1.582.0.f32")[0]==17,"Ownership/read rounds differ");reject([&]{recorder.begin(100001,1);});
    Recorder partial;partial.begin(100000,0);unsigned attempted=0;partial.source(649,1,"{}",b,[&](char*p,size_t n){if(++attempted==2)throw std::runtime_error("Injected read failure");std::memset(p,21,n);});partial.capture(root/"partial","original error");need(std::filesystem::exists(root/"partial/round0.649.1.f32")&&!std::filesystem::exists(root/"partial/round1.649.1.f32"),"Partial read evidence differs");
    Recorder cleared;cleared.begin(100000,0);cleared.source(582,0,"{}",b,[](char*,size_t){});cleared.begin(100001,1);cleared.capture(root/"cleared","later frame");need(!std::filesystem::exists(root/"cleared/host.582.0.f32"),"Previous frame retained");
    std::vector<pose::validation::FixtureWindow> cases(4);for(auto&c:cases){c={};c.name="synthetic";}
    std::vector<pose::measurement::Measurement> values(2);for(size_t i=0;i<2;++i){values[i].item.window.frame_id=100000+i;values[i].result.frame_id=100000+i;values[i].result.invocation=i;}
    values[0].result.poses[123]=0.5546875f;values[1].result.scores[3]=std::numeric_limits<float>::quiet_NaN();
    std::filesystem::create_directory(root/"owned");for(size_t i=0;i<2;++i)pose::owned_results::saveReturned(values[i],i,root/"owned");
    pose::owned_results::save(values,cases,root/"owned");need(read(root/"owned/result0.poses.f32")==read(root/"owned/presaved-results/0/poses.f32"),"Finite bad result lost");need(read(root/"owned/result1.scores.f32")==read(root/"owned/presaved-results/1/scores.f32"),"Nonfinite raw evidence lost");
    reject([&]{pose::measurement::verify(cases[0],values[0].result,values[0].item.window,0);});reject([&]{pose::owned_results::save(values,cases,root/"owned");});
    need(refused==6,"Refusal coverage differs");std::cout<<"{\"status\":\"passed\",\"refusals\":6,\"foreign_thread_refused\":true,\"owned_bytes\":true,\"two_rounds\":true,\"partial_read_saved\":true,\"bad_result_saved\":true,\"previous_frame_cleared\":true,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
