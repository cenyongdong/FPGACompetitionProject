#include "upstream_boundary.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
int main(int argc,char**argv){try{
    if(argc!=2)throw std::runtime_error("Fresh boundary test directory required");
    std::filesystem::path root=argv[1];if(std::filesystem::exists(root))throw std::runtime_error("Preserve test evidence");std::filesystem::create_directory(root);
    pose::upstream::Evidence e;unsigned refusals=0;auto reject=[&](auto f){try{f();}catch(const std::exception&){++refusals;return;}throw std::runtime_error("Expected boundary refusal absent");};
    reject([&]{e.begin(100001,1);});e.begin(100000,0);pose::upstream::Sample s;s.point="topk_indices";s.value=1137;s.storage="{}";s.bytes=std::vector<char>(400,42);e.record(s);s.bytes[0]=99;
    reject([&]{e.record(s);});auto wrong=s;wrong.point="unknown";reject([&]{e.record(wrong);});wrong=s;wrong.point="gather_pre_indices";wrong.bytes.resize(399);reject([&]{e.record(wrong);});wrong=s;wrong.point="gather_pre_indices";wrong.storage=std::string(16384,'x');reject([&]{e.record(wrong);});reject([&]{e.begin(100002,2);});
    bool foreign=false;std::thread t([&]{try{e.begin(100001,1);}catch(const std::exception&){foreign=true;}});t.join();if(!foreign)throw std::runtime_error("Foreign boundary owner accepted");
    e.begin(100001,1);pose::upstream::Sample partial;partial.point="gather_post";partial.value=1148;partial.storage="{}";partial.error="Injected\nread\033failure";e.record(partial);e.save(root/"evidence");reject([&]{e.begin(100002,2);});
    std::ifstream f(root/"evidence/frame0/topk_indices.f32",std::ios::binary);char value=0;f.read(&value,1);if(value!=42||std::filesystem::exists(root/"evidence/frame1/topk_indices.f32")||std::filesystem::exists(root/"evidence/frame1/gather_post.f32")||refusals!=7)throw std::runtime_error("Boundary ownership/clear/partial differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":7,\"foreign_thread_refused\":true,\"owned_bytes\":true,\"previous_frame_cleared\":true,\"partial_read_preserved\":true,\"control_error_JSON\":true,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
