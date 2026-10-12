#include "model_only_run.hpp"
#include "invocation_evidence.hpp"
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace {
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
std::vector<pose::validation::FixtureWindow> fixtures(size_t n){
    std::vector<pose::validation::FixtureWindow>v(n);for(size_t i=0;i<n;++i){v[i].name="fixture"+std::to_string(i);v[i].window.frame_id=6+i;v[i].window.csi[0]={double(i),1};}return v;
}
}
int main(int argc,char**argv){try{
    namespace m=pose::model_only;need(argc==2&&!std::filesystem::exists(argv[1]),"Fresh contract output required");std::filesystem::create_directory(argv[1]);
    unsigned refused=0;auto reject=[&](const std::function<void()>&f){bool bad=false;try{f();}catch(const std::exception&){bad=true;}need(bad,"Invalid model-only contract accepted");++refused;};
    reject([&]{m::Run x(fixtures(3),4);});reject([&]{m::Run x(fixtures(27),104);});reject([&]{m::Run x(fixtures(4),103);});
    reject([&]{m::scheduledStart(1,103,1,200);});reject([&]{m::scheduledStart(1,1,1,0);});reject([&]{m::scheduledStart(UINT64_MAX-1,1,UINT64_MAX-1,4);});
    need(m::scheduledStart(1000,2,2000,200)==2200,"Late schedule burst catchup");
    auto process=[](const pose_v1::Window&w){pose_v1::application::Result r;r.frame_id=w.frame_id;r.input[0]=float(w.csi[0].real());r.scores[0]=3;r.poses[0]=4;return r;};
    m::Run good(fixtures(27),103);for(size_t i=0;i<103;++i){good.step(process,[i](const auto&f,const auto&r){need(r.attempt.index==i&&r.attempt.fixtureFrame==6+i%27&&r.attempt.window.frame_id==100000+i&&f.name=="fixture"+std::to_string(i%27),"Finite source order differs");});}
    need(good.returned().size()==103&&good.returned()[102].verified,"Finite returned coverage differs");reject([&]{good.step(process,[](const auto&,const auto&){});});
    m::Run error(fixtures(4),4);unsigned calls=0;
    try{error.step([&](const auto&)->pose_v1::application::Result{++calls;throw std::runtime_error("original computation");},[](const auto&,const auto&){});throw std::runtime_error("Missing compute error");}catch(const std::exception&e){need(std::string(e.what())=="original computation","Original compute error replaced");}
    reject([&]{error.step(process,[](const auto&,const auto&){});});need(calls==1&&error.attempts()==1&&error.returned().empty()&&error.current()->window.frame_id==100000,"Compute failure retried or owned window lost");
    m::Run gate(fixtures(4),4);try{gate.step(process,[](const auto&,const auto&){throw std::runtime_error("original gate");});throw std::runtime_error("Missing gate error");}catch(const std::exception&e){need(std::string(e.what())=="original gate","Original gate error replaced");}
    reject([&]{gate.step(process,[](const auto&,const auto&){});});need(gate.returned().size()==1&&!gate.returned()[0].verified&&gate.returned()[0].result.scores[0]==3,"Returned error bytes lost");
    auto owned=good.returned()[0];owned.result.scores[0]=99;owned.attempt.window.csi[0]={99,99};need(good.returned()[0].result.scores[0]==3&&good.returned()[0].attempt.window.csi[0].real()==0,"Returned bytes alias caller");
    std::exception_ptr original=std::make_exception_ptr(std::runtime_error("original gate"));bool later=false;
    pose::invocation_evidence::flush({{"failed-task",[]{throw std::runtime_error("storage error");}},{"later-owned",[&]{std::ofstream f(std::filesystem::path(argv[1])/"owned.f32",std::ios::binary);f.write(reinterpret_cast<const char*>(gate.returned()[0].result.scores.data()),sizeof(gate.returned()[0].result.scores));need(bool(f),"Owned bytes save failed");later=true;}}},original,std::filesystem::path(argv[1])/"ledger.json");
    need(later,"Independent later persistence skipped");try{std::rethrow_exception(original);}catch(const std::exception&e){need(std::string(e.what())=="original gate","Flush replaced original error");}
    need(refused==9,"Model-only refusal count differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":9,\"scheduled_windows\":103,\"owned_values\":true,\"no_calls_after_error\":true,\"no_burst_catchup\":true,\"independent_flush\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
