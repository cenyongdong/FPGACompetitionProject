// SDK-free, runs on FPAI host x86 after returned results are independently verified.
#include "skeleton_render.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
namespace {
template<size_t N> std::array<float,N> read(const std::filesystem::path& path){
    std::array<float,N> data{};std::ifstream f(path,std::ios::binary);
    if(!f||std::filesystem::file_size(path)!=N*4||!f.read(reinterpret_cast<char*>(data.data()),N*4))throw std::runtime_error("Reference tensor bytes differ");
    return data;
}
void write(const std::filesystem::path& path,const std::vector<uint8_t>& bytes){
    std::ofstream f(path,std::ios::binary);f.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());f.close();
    if(!f)throw std::runtime_error("Reference image write failed");
}
}
int main(int argc,char** argv){try{
    namespace fs=std::filesystem;namespace rr=pose_v1::render;
    if(argc!=4||fs::exists(argv[3]))throw std::runtime_error("reference-export TSV TENSORS FRESH-OUTPUT");
    const fs::path inputs=argv[2],out=argv[3];fs::create_directory(out);
    std::ifstream plan(argv[1]);if(!plan)throw std::runtime_error("Reference plan open failed");
    auto warm=rr::draw({}, {},0,rr::Status::NoInput);write(out/"warmup.nv12",rr::yuv420sp(warm.rgb,rr::width,rr::height,false));
    size_t invocation=0,count=0;uint64_t frame=0;
    while(plan>>invocation>>frame){
        if(invocation!=count||count>=103)throw std::runtime_error("Reference plan order/budget differs");
        auto scores=read<100>(inputs/("result"+std::to_string(count)+".scores.f32"));
        auto poses=read<4200>(inputs/("result"+std::to_string(count)+".poses.f32"));
        auto rgb=rr::draw(scores,poses,frame);write(out/("result"+std::to_string(count)+".nv12"),rr::yuv420sp(rgb.rgb,rr::width,rr::height,false));++count;
    }
    if(!plan.eof()||!count)throw std::runtime_error("Reference plan incomplete");
    std::cout<<"{\"frames\":"<<count<<",\"SDK_device\":false,\"reference_reconstruction\":true}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
