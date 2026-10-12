#include "producer_payload.hpp"
#include <cstring>
#include <iostream>
#include <limits>
namespace {void rejected(const pose::producer::Payload&p){try{pose::producer::validate(p);}catch(const std::exception&){return;}throw std::runtime_error("Invalid payload accepted");}}
int main(int argc,char**argv){try{
    using namespace pose::producer;need(argc==2,"Pattern root required");
    auto a=load(std::filesystem::path(argv[1])/"pattern-0"),b=load(std::filesystem::path(argv[1])/"pattern-1");
    need(a.inputs!=b.inputs&&a.expected!=b.expected,"Patterns not distinguishable");
    auto original=a.inputs;auto owned=a;owned.inputs[0][0]^=1;need(a.inputs==original,"Byte ownership failed");
    auto bad=a;bad.inputs[0].pop_back();rejected(bad);
    bad=a;bad.expected[1].pop_back();rejected(bad);
    for(float v:{-1.f,180.f,0.5f,std::numeric_limits<float>::infinity(),std::numeric_limits<float>::quiet_NaN()}){
        bad=a;std::memcpy(bad.inputs[0].data(),&v,4);rejected(bad);
    }
    bad=a;uint16_t inf=0x7c00;std::memcpy(bad.inputs[1].data(),&inf,2);rejected(bad);
    bad=a;float inf32=std::numeric_limits<float>::infinity();std::memcpy(bad.expected[0].data(),&inf32,4);rejected(bad);
    std::cout<<"Payload ownership, two pinned patterns and nine rejection contracts passed.\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
