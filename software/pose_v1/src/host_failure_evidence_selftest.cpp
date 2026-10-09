#include "host_failure_evidence.hpp"
#include <fstream>
#include <iostream>
#include <cstring>
#include <limits>
#include <stdexcept>
int main(int argc,char** argv){try{
    if(argc!=2)throw std::runtime_error("Fresh failure-test directory required");
    namespace ev=pose::failure_evidence;
    ev::configure(argv[1]);size_t rejected=0;
    auto refuse=[&](auto fn){try{fn();}catch(const std::exception&){++rejected;return;}throw std::runtime_error("Invalid failure contract accepted");};
    refuse([&]{ev::configure(argv[1]);});
    ev::Blob b;b.shape={1,4};b.layout="*C";b.chunkBytes=16;b.bytes.resize(16);
    uint32_t bits[]={0,0x80000000,0x7fc12345,0x3f000000};std::memcpy(b.bytes.data(),bits,16);
    refuse([&]{ev::save(1,0,192,"bad",{},"[]");});
    auto invalid=b;invalid.slot=1;refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    invalid=b;invalid.chunkBytes=15;refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    invalid=b;invalid.shape={-1,4};refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    invalid=b;invalid.shape={2,4};refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    invalid=b;invalid.shape={std::numeric_limits<int64_t>::max(),4};refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    invalid=b;invalid.bytes.resize(1024*1024+4);invalid.chunkBytes=invalid.bytes.size();invalid.shape={262145};refuse([&]{ev::save(1,0,192,"bad",{invalid},"[]");});
    ev::save(1,0,192,"quote\"\n",{b},"[]");std::memset(b.bytes.data(),1,16);
    std::ifstream f(std::filesystem::path(argv[1])/"input0.f32",std::ios::binary);char actual[16];f.read(actual,16);
    if(!f||std::memcmp(actual,bits,16)!=0)throw std::runtime_error("Failure byte ownership differs");
    refuse([&]{ev::save(1,0,192,"duplicate",{b},"[]");});
    std::cout<<"{\"status\":\"passed\",\"rejections\":"<<rejected<<",\"owned_FP32_bytes\":16,\"SDK_device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
