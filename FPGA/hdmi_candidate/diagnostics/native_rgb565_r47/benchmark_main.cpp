// CPU-only ordinary-memory renderer checks and timing. No SDK, MMIO or BOOT.
#include "skeleton_render.hpp"
#include "hdmi_canvas.hpp"
#include "hdmi_renderer.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>
namespace {
void need(bool yes,const char* why){if(!yes)throw std::runtime_error(why);}
using Clock=std::chrono::steady_clock;
double elapsed(Clock::time_point a,Clock::time_point b){return std::chrono::duration<double,std::milli>(b-a).count();}
template<class A>void read(const std::string& p,A& a){std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(a.data()),sizeof(a));need(bool(f),"Frozen renderer fixture incomplete");need(f.peek()==EOF,"Frozen renderer fixture has surplus bytes");}
void save(const std::string& p,const std::vector<uint8_t>& bytes){std::ofstream f(p,std::ios::binary);f.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());need(bool(f),"Cannot save ordinary-memory image");}
struct Sample{double draw,canvas,native;};
void stats(const char* name,std::vector<double> v){std::sort(v.begin(),v.end());double sum=0;for(auto x:v)sum+=x;std::cout<<"\""<<name<<"\":{\"mean_ms\":"<<sum/v.size()<<",\"median_ms\":"<<v[v.size()/2]<<",\"p95_ms\":"<<v[(v.size()*95-1)/100]<<",\"max_ms\":"<<v.back()<<"}";}
}
int main(int argc,char** argv){try{
    need(argc==4,"renderer_bench FIXTURES OUTPUT REPEATS");
    const std::string fixtures=argv[1],out=argv[2];const int repeats=std::stoi(argv[3]);
    need(repeats>=3&&repeats<=60,"Bounded ordinary-memory repeats required");
    std::array<float,100> scores{};std::array<float,4200> poses{};
    std::vector<double> draw,canvas,native;unsigned checked=0;double cold_native=0;
    for(int fixture=0;fixture<3;++fixture){
        const std::string id=std::to_string(308+fixture);
        read(fixtures+"/S11_01_"+id+".scores.f32",scores);read(fixtures+"/S11_01_"+id+".poses.f32",poses);
        const auto saved_scores=scores;const auto saved_poses=poses;
        for(int i=0;i<repeats;++i){
            const uint64_t frame_id=1000000+fixture*repeats+i;
            auto t0=Clock::now();auto old=pose_v1::render::draw(scores,poses,frame_id);
            auto t1=Clock::now();auto old565=pose::hdmi::canvas(old.rgb);auto t2=Clock::now();
            auto result=pose::hdmi::render(scores,poses,frame_id);auto t3=Clock::now();
            need(result.rgb565.size()==4147200,"Native 1080p RGB565 byte count differs");
            need(result.top_index==old.top_index&&result.score==old.score&&result.selected_raw==old.selected_raw,
                 "Native renderer altered model values or candidate selection");
            for(size_t j=0;j<14;++j){
                auto p=pose_v1::render::project(result.selected_raw[j*3],result.selected_raw[j*3+1],result.selected_raw[j*3+2]);
                // Larger viewport, unchanged physical skeleton scale (220*1.5).
                need(std::abs(result.projected[j][0]-(780+(p[0]-460)*1.5))<1e-9&&
                     std::abs(result.projected[j][1]-(535+(p[1]-355)*1.5))<1e-9,
                     "Native skeleton size/projection changed");
            }
            need(scores==saved_scores&&poses==saved_poses,"Renderer mutated inference arrays");
            if(fixture==0&&i==0)cold_native=elapsed(t2,t3);
            else {draw.push_back(elapsed(t0,t1));canvas.push_back(elapsed(t1,t2));native.push_back(elapsed(t2,t3));}
            if(i==0){save(out+"/old-"+id+".rgb565",old565);save(out+"/native-"+id+".rgb565",result.rgb565);}
            ++checked;
        }
    }
    for(auto status:{pose_v1::render::Status::NoInput,pose_v1::render::Status::Stopped}){
        auto r=pose::hdmi::render(scores,poses,42,status);need(r.rgb565.size()==4147200,"Status image differs");++checked;
    }
    scores[0]=std::numeric_limits<float>::quiet_NaN();bool refused=false;
    try{pose::hdmi::render(scores,poses,0);}catch(const std::exception&){refused=true;}
    need(refused,"NaN renderer input accepted");
    std::cout<<"{\"CPU_only\":true,\"SDK\":0,\"MMIO\":0,\"checked\":"<<checked<<",\"model_values_preserved\":true,\"skeleton_scale_preserved\":true,\"native_first_call_ms\":"<<cold_native<<",";
    stats("old_draw",draw);std::cout<<",";stats("old_canvas",canvas);std::cout<<",";stats("native_RGB565",native);std::cout<<"}\n";
    return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
