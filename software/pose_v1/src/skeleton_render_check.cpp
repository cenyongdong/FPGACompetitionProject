#include "skeleton_render.hpp"
#include <algorithm>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>

namespace r=pose_v1::render;namespace fs=std::filesystem;
static void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
static void write(const fs::path&p,const std::vector<uint8_t>&b){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());need(bool(f),"Raster write failed");}
template<size_t N>static std::array<float,N> read(const fs::path&p){std::ifstream f(p,std::ios::binary|std::ios::ate);need(bool(f)&&f.tellg()==N*4,"Invalid FP32 array bytes");std::array<float,N>a;f.seekg(0);f.read(reinterpret_cast<char*>(a.data()),sizeof(a));need(bool(f),"Cannot read FP32 array");return a;}
static void persist(const fs::path&out,const std::string&stem,const r::Frame&f){
    std::ofstream ppm(out/(stem+".ppm"),std::ios::binary);ppm<<"P6\n1280 720\n255\n";ppm.write(reinterpret_cast<const char*>(f.rgb.data()),f.rgb.size());need(bool(ppm),"PPM write failed");
    auto begin=std::chrono::steady_clock::now();auto rgb565=r::rgb565_le(f.rgb,r::width,r::height),nv12=r::yuv420sp(f.rgb,r::width,r::height,false),nv21=r::yuv420sp(f.rgb,r::width,r::height,true);double convert=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
    write(out/(stem+".rgb565le"),rgb565);write(out/(stem+".nv12"),nv12);write(out/(stem+".nv21"),nv21);
    std::ofstream meta(out/(stem+".json"));meta<<std::setprecision(17)<<"{\"frame_id\":"<<f.frame_id<<",\"top_index\":"<<f.top_index<<",\"score\":"<<f.score<<",\"render_ms\":"<<f.render_ms<<",\"three_format_conversion_ms\":"<<convert<<",\"clipped_joints\":"<<f.clipped_joints<<",\"selected_raw\":[";
    for(size_t i=0;i<42;++i){if(i)meta<<',';meta<<f.selected_raw[i];}meta<<"],\"projected\":[";for(size_t i=0;i<14;++i){if(i)meta<<',';meta<<'['<<f.projected[i][0]<<','<<f.projected[i][1]<<']';}meta<<"]}\n";need(bool(meta),"Metadata write failed");
}
static void self_test(const fs::path&out){
    std::array<float,100>s{};std::array<float,4200>p{};s[3]=s[4]=0.75f;
    const std::array<std::array<float,3>,14>body{{{1.75,1.75,2.75},{1.75,1.75,2.6},{1.95,1.75,2.8},{1.55,1.75,2.8},{2.1,1.75,3.1},{1.9,1.75,3.3},{1.4,1.75,3.1},{1.6,1.75,3.3},{2.15,1.75,3.45},{1.9,1.75,3.7},{1.35,1.75,3.45},{1.6,1.75,3.7},{1.9,1.75,4.05},{1.6,1.75,4.05}}};
    for(size_t i=0;i<14;++i)std::copy(body[i].begin(),body[i].end(),p.begin()+3*42+i*3);
    auto original_s=s;auto original_p=p;auto f=r::draw(s,p,999);need(f.top_index==3&&std::memcmp(p.data(),original_p.data(),sizeof(p))==0&&std::memcmp(s.data(),original_s.data(),sizeof(s))==0,"Selection/tie or input mutation");persist(out,"synthetic",f);
    std::vector<uint8_t> colors={255,0,0,0,255,0,0,0,255,255,255,255};write(out/"colors.rgb24",colors);write(out/"colors.rgb565le",r::rgb565_le(colors,2,2));write(out/"colors.nv12",r::yuv420sp(colors,2,2,false));write(out/"colors.nv21",r::yuv420sp(colors,2,2,true));
    size_t refused=0;auto reject=[&](auto action){try{action();}catch(const std::exception&){++refused;return;}throw std::runtime_error("Invalid rendering accepted");};
    auto bad_s=s;bad_s[90]=std::numeric_limits<float>::quiet_NaN();reject([&]{r::draw(bad_s,p,0);});bad_s=s;bad_s[0]=std::numeric_limits<float>::infinity();reject([&]{r::draw(bad_s,p,0);});
    auto bad_p=p;bad_p.back()=std::numeric_limits<float>::quiet_NaN();reject([&]{r::draw(s,bad_p,0);});bad_p=p;bad_p[126]=-std::numeric_limits<float>::infinity();reject([&]{r::draw(s,bad_p,0);});
    reject([&]{r::rgb565_le(colors,3,2);});reject([&]{r::yuv420sp(colors,1,4,false);});reject([&]{r::yuv420sp({},0,0,false);});reject([&]{r::draw(s,p,0,static_cast<r::Status>(99));});
    auto huge=p;for(size_t i=126;i<168;++i)huge[i]=std::numeric_limits<float>::max();auto clipped=r::draw(s,huge,1000);need(clipped.clipped_joints==14,"Out-of-view finite pose not clipped");persist(out,"clipped",clipped);
    auto a=r::draw(s,p,1001,r::Status::NoInput),b=r::draw(s,p,1002,r::Status::Stopped);persist(out,"no-input",a);persist(out,"stopped",b);
    need(refused==8,"Rejection count");std::ofstream m(out/"self-test.json");m<<"{\"status\":\"passed\",\"rejections\":8,\"ties_first_slot\":true,\"input_unchanged\":true,\"finite_outside_view_clipped\":true,\"synthetic_not_anatomical_GT\":true}\n";
}
int main(int argc,char**argv){try{
    need(argc==3||argc==4,"Usage: render --self-test OUTPUT | render CATALOG INPUT_FOLDER OUTPUT");
    if(std::string(argv[1])=="--self-test"){need(argc==3,"Self-test argument count");fs::path out=argv[2];need(!fs::exists(out),"Preserve render self-test");fs::create_directory(out);self_test(out);std::cout<<"Renderer self-test passed\n";return 0;}
    need(argc==4,"Catalog argument count");fs::path cat=argv[1],input=argv[2],out=argv[3];need(!fs::exists(out),"Preserve rendered frames");fs::create_directory(out);std::ifstream f(cat);need(bool(f),"Missing render catalog");std::string row;size_t count=0;
    while(std::getline(f,row)){need(count<64,"Render catalog limit exceeded");std::istringstream fields(row);std::string stem,extra;uint64_t frame;need(bool(fields>>stem>>frame)&&!(fields>>extra)&&stem.find_first_not_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")==std::string::npos,"Unsafe catalog");
        auto s=read<100>(input/(stem+".scores.f32"));auto p=read<4200>(input/(stem+".poses.f32"));persist(out,stem,r::draw(s,p,frame));++count;}
    need(count>0&&count<=64,"Render catalog size");std::ofstream summary(out/"summary.json");summary<<"{\"frames\":"<<count<<",\"CPU_only\":true,\"width\":1280,\"height\":720,\"HDMI_VPU_initialized\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
