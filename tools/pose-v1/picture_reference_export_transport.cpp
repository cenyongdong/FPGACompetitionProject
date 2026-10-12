// Native replay of the frozen renderer from actual owned inference outputs.
#include "skeleton_render.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
namespace {
void need(bool b,const char*s){if(!b){throw std::runtime_error(s);}}
template<size_t N>void read(const std::filesystem::path&p,std::array<float,N>& a){std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(a.data()),sizeof(a));need(bool(f)&&f.peek()==EOF,"Reference FP32 bytes differ");}
void write(const std::filesystem::path&p,const std::vector<uint8_t>& a){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(a.data()),a.size());f.close();need(bool(f),"Native picture write failed");}
}
int main(int argc,char**argv){try{
    need(argc==4,"RESULTS FRESH-REFERENCE COUNT");const std::filesystem::path in=argv[1],out=argv[2];unsigned count=std::stoul(argv[3]);need(count<=107&&!std::filesystem::exists(out),"Preserve native references");std::filesystem::create_directory(out);
    std::array<float,100> scores{};std::array<float,4200> poses{};auto warm=pose_v1::render::draw(scores,poses,0,pose_v1::render::Status::NoInput);write(out/"warmup.nv12",pose_v1::render::yuv420sp(warm.rgb,1280,720,false));
    std::ifstream ids(in/"transport-ids.txt");need(bool(ids),"Transport identity file missing");
    for(unsigned i=0;i<count;++i){uint64_t id=0;need(bool(ids>>id),"Transport identity missing");auto name="result"+std::to_string(i);read(in/(name+".scores.f32"),scores);read(in/(name+".poses.f32"),poses);auto frame=pose_v1::render::draw(scores,poses,id);write(out/(name+".nv12"),pose_v1::render::yuv420sp(frame.rgb,1280,720,false));}
    std::cout<<"Native frozen renderer exported "<<count<<" complete owned pictures.\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
