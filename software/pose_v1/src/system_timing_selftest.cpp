#include "system_timing.hpp"
#include <iostream>
#include <cstring>
#include <limits>

int main(){try{
    std::vector<pose::validation::FixtureWindow> cases(27);
    for(size_t i=0;i<cases.size();++i){cases[i].window.frame_id=10+i;cases[i].scores[0]=float(i);}
    unsigned refused=0;auto reject=[&](auto action){try{action();}catch(const std::exception&){++refused;return;}throw std::runtime_error("Expected refusal missing");};
    if(&pose::measurement::fixtureFor(cases,100032)!=&cases[5])throw std::runtime_error("Transport mapping differs");
    reject([&]{pose::measurement::fixtureFor(cases,99999);});reject([&]{pose::measurement::fixtureFor(cases,100033);});
    pose_v1::Window actual=cases[5].window;actual.frame_id=100032;
    pose_v1::application::Result r;r.frame_id=actual.frame_id;r.input=cases[5].input;r.scores=cases[5].scores;r.poses=cases[5].poses;r.completed_layers=745;r.host_callbacks=r.zg_callbacks=7;
    pose::measurement::verify(cases[5],r,actual,0);
    auto bad=r;bad.invocation=32;reject([&]{pose::measurement::verify(cases[5],bad,actual,0);});
    bad=r;bad.scores[0]=std::numeric_limits<float>::quiet_NaN();reject([&]{pose::measurement::verify(cases[5],bad,actual,0);});
    bad=r;bad.poses[0]=1;reject([&]{pose::measurement::verify(cases[5],bad,actual,0);});
    bad=r;bad.completed_layers=744;reject([&]{pose::measurement::verify(cases[5],bad,actual,0);});
    auto changed=actual;changed.csi[0]={1,0};reject([&]{pose::measurement::verify(cases[5],r,changed,0);});
    std::cout<<"{\"status\":\"passed\",\"rejections\":"<<refused<<",\"transport_fixture_separate\":true,\"device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
