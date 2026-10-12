#include "resident_sequence.hpp"
#include "model_load_lifecycle.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {void need(bool ok,const char* why){if(!ok){throw std::runtime_error(why);}}}
int main(){try{
    namespace s=pose::resident_sequence;unsigned refused=0,starts=0,ready=0,joins=0,stops=0;bool engine=false;
    auto reject=[&](auto f){try{f();}catch(const std::exception&){++refused;return;}throw std::runtime_error("Missing sequence refusal");};
    pose::load_lifecycle::Control load(true,{[&]{++starts;},[&]{++ready;},[]{},[&]{need(engine,"Engine released before worker join");++joins;},[&](bool abort){need(!abort,"Unexpected normal abort");++stops;}});
    s::Sequence normal;reject([&]{normal.invocation();});load.start();engine=true;std::vector<size_t> ids;
    for(size_t phase=0;phase<2;++phase){
        auto p=normal.begin();need(p.offset==(phase?4:0)&&p.count==(phase?103:4)&&p.period==500000000,"Stage specification changed");
        reject([&]{normal.begin();});reject([&]{normal.advance();});
        for(size_t i=0;i<p.count;++i){load.check();ids.push_back(normal.invocation());normal.completeCall();}
        reject([&]{normal.completeCall();});normal.advance();need(starts==1&&ready==1&&joins==0&&stops==0&&engine,"Resource restarted at stage boundary");
    }
    need(normal.done()&&ids.size()==107,"Sequence incomplete");for(size_t i=0;i<ids.size();++i){need(ids[i]==i,"Invocation collision");}
    reject([&]{normal.begin();});std::exception_ptr error;load.finish(error);need(!error&&load.joined()&&joins==1&&stops==1,"Single lifecycle cleanup differs");engine=false;
    s::Sequence failed;failed.begin();failed.completeCall();failed.stop();reject([&]{failed.invocation();});reject([&]{failed.completeCall();});reject([&]{failed.advance();});reject([&]{failed.begin();});need(!failed.done(),"Failed sequence passed");
    s::Sequence foreign;bool ownerRefused=false;std::thread other([&]{try{foreign.begin();}catch(const std::exception&){ownerRefused=true;}});other.join();need(ownerRefused,"Foreign owner accepted");++refused;
    std::cout<<"{\"status\":\"passed\",\"refusals\":"<<refused<<",\"calls\":107,\"unique_invocations\":true,\"load_starts\":1,\"load_joins\":1,\"no_boundary_resource_restart\":true,\"failure_stops_next_stage\":true,\"SDK_device\":false}\n";
    return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
