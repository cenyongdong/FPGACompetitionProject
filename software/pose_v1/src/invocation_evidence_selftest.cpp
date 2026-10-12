#include "invocation_evidence.hpp"
#include <array>
#include <cstring>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace {void need(bool x,const char* m){if(!x)throw std::runtime_error(m);}}
int main(int argc,char** argv){try{
    namespace e=pose::invocation_evidence;namespace fs=std::filesystem;need(argc==2&&!fs::exists(argv[1]),"Use fresh selftest output");fs::path out=argv[1];fs::create_directory(out);unsigned rejected=0;
    auto reject=[&](auto f){try{f();}catch(const std::exception&){++rejected;return;}throw std::runtime_error("Expected refusal missing");};
    e::Frame frame;reject([&]{frame.record(582,0,std::vector<char>(16));});frame.begin(100037,37);
    const std::array<uint32_t,4> original{0xffffffff,0x80000000,0x3f800000,0x40000000};
    {std::vector<char> temporary(16);std::memcpy(temporary.data(),original.data(),16);frame.record(582,0,temporary);temporary.assign(16,0);}
    need(frame.bytes()==16&&frame.inputs()==1,"Frame retention count differs");
    reject([&]{frame.record(582,0,std::vector<char>(16));});reject([&]{frame.record(582,1,{});});reject([&]{frame.record(582,1,std::vector<char>(3));});reject([&]{frame.record(582,4,std::vector<char>(4));});
    reject([&]{frame.begin(100038,37);});reject([&]{frame.begin(100036,36);});reject([&]{frame.record(582,1,std::vector<char>(1048576));});
    std::exception_ptr failure=std::make_exception_ptr(std::runtime_error("Timing actual model output differs"));bool metadata=false,cleanup=false;
    e::flush({{"repeat_output_gate",[]{throw std::runtime_error("repeat comparison\nthrows");}},
              {"Host_frame",[&]{frame.save(out/"Host-frame");}},
              {"metadata",[&]{std::ofstream(out/"metadata.txt")<<"preserved";metadata=true;}},
              {"cleanup",[&]{std::ofstream(out/"cleanup.txt")<<"completed";cleanup=true;}}},failure,out/"flush-ledger.json");
    need(metadata&&cleanup,"Failure prevented independent persistence");bool preserved=false;try{std::rethrow_exception(failure);}catch(const std::runtime_error& x){preserved=std::string(x.what())=="Timing actual model output differs";}need(preserved,"Original computation error replaced");
    std::array<uint32_t,4> actual{};std::ifstream input(out/"Host-frame/op582.slot0.f32",std::ios::binary);input.read(reinterpret_cast<char*>(actual.data()),16);need(bool(input)&&actual==original,"Released producer bytes were not retained");
    reject([&]{frame.save(out/"Host-frame");});frame.begin(100038,38);need(frame.bytes()==0&&frame.inputs()==0,"New invocation retained old frame");
    for(int i=0;i<8;++i)frame.record(i,0,std::vector<char>(4));
    reject([&]{frame.record(9,0,std::vector<char>(4));});
    bool wrongOwnerRejected=false;std::thread other([&]{try{frame.begin(100039,39);}catch(const std::runtime_error&){wrongOwnerRejected=true;}});other.join();need(wrongOwnerRejected,"Wrong owner thread was accepted");++rejected;
    std::exception_ptr normal;unsigned completed=0;e::flush({{"normal_a",[&]{++completed;}},{"normal_b",[&]{++completed;}}},normal,out/"normal-ledger.json");need(!normal&&completed==2,"Normal flush failed");
    reject([&]{e::flush({},normal,out/"invalid-ledger.json");});
    std::cout<<"{\"status\":\"passed\",\"refusals\":"<<rejected<<",\"owned_bytes_after_producer_release\":16,\"all_tasks_after_comparison_error\":true,\"original_error_preserved\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
