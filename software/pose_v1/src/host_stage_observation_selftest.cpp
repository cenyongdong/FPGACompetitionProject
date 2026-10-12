#include "host_stage_observation.hpp"
#include <array>
#include <fstream>
#include <iostream>
#include <cstring>
namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
int main(int argc,char** argv){try{
    namespace s=pose::stage_observation;namespace fs=std::filesystem;
    need(argc==2&&!fs::exists(argv[1]),"stage-selftest FRESH-OUTPUT");fs::path out=argv[1];fs::create_directory(out);s::configure(out/"observations");unsigned rejected=0;
    auto reject=[&](auto f){try{f();}catch(const std::exception&){++rejected;return;}throw std::runtime_error("Expected stage refusal missing");};
    std::array<uint32_t,3> counts{481,637,638};size_t next=0;
    auto ready=s::waitFresh(638,745,[&]{return counts[next++];},std::chrono::milliseconds(100));need(ready.polls==3&&ready.initial==481&&ready.final==638,"Fresh counter wait differs");
    s::recordCompletion(1,0,582,ready);
    reject([&]{s::waitFresh(638,745,[]{return 637;},std::chrono::milliseconds(0));});
    next=0;reject([&]{s::waitFresh(638,745,[&]{return next++?600:637;},std::chrono::milliseconds(100));});
    reject([&]{s::waitFresh(638,745,[]{return 746;},std::chrono::milliseconds(100));});
    reject([&]{s::waitFresh(0,745,[]{return 638;},std::chrono::milliseconds(100));});
    alignas(64) std::array<uint32_t,4> data{0xffffffff,0x80000000,0x3f800000,0x40000000};const auto original=data;
    s::Info info;info.bytes=16;info.hostPointer=reinterpret_cast<uintptr_t>(data.data());info.hostChunk=3;info.hostCapacity=info.sourceCapacity=16;info.sourceKind="CPTR";info.hostRegion=info.sourceRegion="Host";info.copyBegin=1;info.copyEnd=2;
    s::Call capture(1,0,192);capture.afterCopy(info,reinterpret_cast<char*>(data.data()));capture.validate();data.fill(0);fs::create_directory(out/"saved-host");capture.saveFailure(out/"saved-host",s::now());
    std::array<uint32_t,4> recovered{};std::ifstream f(out/"saved-host/post-copy/input0.f32",std::ios::binary);f.read(reinterpret_cast<char*>(recovered.data()),16);need(bool(f)&&recovered==original,"Shadow did not own original NaN/negative-zero bytes");
    auto test=[&](s::Info bad,const char* pointer){s::Call c(1,0,192);c.afterCopy(bad,pointer);c.validate();};
    auto bad=info;bad.hostCapacity=15;reject([&]{test(bad,reinterpret_cast<char*>(data.data()));});
    bad=info;bad.sourceCapacity=15;reject([&]{test(bad,reinterpret_cast<char*>(data.data()));});
    bad=info;bad.sourceKind="ADDR";bad.sourceAddress=3;reject([&]{test(bad,reinterpret_cast<char*>(data.data()));});
    bad=info;bad.bytes=15;reject([&]{test(bad,reinterpret_cast<char*>(data.data()));});
    alignas(64) std::array<char,20> unaligned{};bad=info;bad.bytes=4;bad.hostPointer=reinterpret_cast<uintptr_t>(unaligned.data()+1);reject([&]{test(bad,unaligned.data()+1);});
    reject([&]{s::Call c(1,0,192);c.afterCopy(info,reinterpret_cast<char*>(data.data()));c.afterCopy(info,reinterpret_cast<char*>(data.data()));c.validate();});
    bad=info;bad.bytes=0;reject([&]{test(bad,reinterpret_cast<char*>(data.data()));});
    s::saveMetadata();std::cout<<"{\"status\":\"passed\",\"refusals\":"<<rejected<<",\"owned_bytes\":16,\"fresh_counter_polls\":3,\"SDK_device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
