#include "model_load_lifecycle.hpp"
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
void errorIs(std::exception_ptr p,const std::string&text){need(bool(p),"Original error absent");try{std::rethrow_exception(p);}catch(const std::exception&e){need(e.what()==text,"Original error replaced");}}
}
int main(){try{
    namespace l=pose::load_lifecycle;unsigned refusals=0;auto reject=[&](const std::function<void()>&f){bool b=false;try{f();}catch(const std::exception&){b=true;}need(b,"Invalid load lifecycle accepted");++refusals;};
    reject([&]{l::Control bad(true,{});});std::vector<std::string>events;bool abort=false;
    l::Hooks h{[&]{events.push_back("start");},[&]{events.push_back("ready");},[&]{events.push_back("check");},[&]{events.push_back("join");},[&](bool b){abort=b;events.push_back("stop");}};
    l::Control good(true,h);reject([&]{good.check();});good.start();reject([&]{good.start();});good.check();std::exception_ptr p;good.finish(p);
    need(!p&&!abort&&good.joined()&&events==std::vector<std::string>({"start","ready","check","check","stop","join","check"}),"Normal load cleanup order differs");
    reject([&]{good.check();});reject([&]{good.finish(p);});
    events.clear();l::Control without(false,{});without.start();without.check();without.finish(p);need(events.empty()&&without.joined(),"Disabled load invoked hooks");
    auto failing=h;failing.requestStop=[&](bool b){abort=b;events.push_back("stop-error");throw std::runtime_error("stop error");};failing.join=[&]{events.push_back("join-error");throw std::runtime_error("join error");};
    events.clear();l::Control original(true,failing);original.start();p=std::make_exception_ptr(std::runtime_error("original model error"));original.finish(p);errorIs(p,"original model error");need(abort&&original.joined()&&events.back()=="check","Failure cleanup skipped join/check");
    events.clear();l::Control first(true,failing);first.start();p={};first.finish(p);errorIs(p,"stop error");need(first.joined()&&events.back()=="check","First cleanup error not preserved");
    auto startup=h;startup.waitReady=[]{throw std::runtime_error("first capture error");};events.clear();l::Control partial(true,startup);try{partial.start();throw std::runtime_error("Missing startup error");}catch(const std::exception&e){need(std::string(e.what())=="first capture error","Startup error replaced");p=std::current_exception();}
    partial.finish(p);errorIs(p,"first capture error");need(abort&&partial.joined()&&events==std::vector<std::string>({"start","stop","join","check"}),"Partial startup not cleaned");
    l::Control cross(false,{});bool refused=false;std::thread worker([&]{try{cross.start();}catch(const std::exception&){refused=true;}});worker.join();need(refused,"Cross owner accepted");++refusals;
    need(refusals==6,"Lifecycle refusal count differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":6,\"normal_join_before_engine_release\":true,\"disabled_hooks_not_called\":true,\"partial_start_cleanup\":true,\"original_error_preserved\":true,\"all_cleanup_hooks_attempted\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
