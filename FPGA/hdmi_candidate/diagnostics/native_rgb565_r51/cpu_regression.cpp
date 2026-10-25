// Ordinary-memory regression only. No SDK, MMIO, network or board execution.
#include "hdmi_renderer.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>
namespace {
using Clock=std::chrono::steady_clock;
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
double elapsed(Clock::time_point a,Clock::time_point b){return std::chrono::duration<double,std::milli>(b-a).count();}
template<class A>void load(const std::filesystem::path& p,A& value){
 std::ifstream f(p,std::ios::binary);f.read(reinterpret_cast<char*>(value.data()),value.size()*sizeof(value[0]));
 need(bool(f)&&f.peek()==EOF,"Incomplete/surplus ordinary-memory fixture or golden image");
}
void same(const pose::hdmi::Rendered& a,const pose::hdmi::Rendered& b){
 need(a.rgb565==b.rgb565,"Two-phase RGB565 bytes differ from original render API");
 need(a.top_index==b.top_index&&a.clipped_joints==b.clipped_joints&&
      !std::memcmp(&a.score,&b.score,sizeof(a.score))&&
      !std::memcmp(a.selected_raw.data(),b.selected_raw.data(),sizeof(a.selected_raw))&&
      a.projected==b.projected,"Non-timing renderer fields differ");
}
void stats(const char* name,const std::vector<double>& values){
 double sum=0;for(auto value:values)sum+=value;
 std::cout<<"\""<<name<<"\":{\"count\":"<<values.size()<<",\"mean_ms\":"<<sum/values.size()
          <<",\"max_ms\":"<<*std::max_element(values.begin(),values.end())<<"}";
}
}
int main(int argc,char** argv){try{
 need(argc==3,"renderer_overlap_bench FIXTURES GOLDEN_CPU_OUTPUT");
 const std::filesystem::path fixtures(argv[1]),golden(argv[2]);
 std::vector<double> preparation,dynamic,original;unsigned checks=0,golden_checks=0;
 for(unsigned fixture=0;fixture<3;++fixture){
  const auto suffix=std::to_string(308+fixture);std::array<float,100> scores{};std::array<float,4200> poses{};
  load(fixtures/("S11_01_"+suffix+".scores.f32"),scores);load(fixtures/("S11_01_"+suffix+".poses.f32"),poses);
  const auto saved_scores=scores;const auto saved_poses=poses;const uint64_t id=1000000+10*fixture;
  for(auto status:{pose_v1::render::Status::Result,pose_v1::render::Status::NoInput,pose_v1::render::Status::Stopped}){
   auto begin=Clock::now();auto ordinary=pose::hdmi::render(scores,poses,id,status);auto old_end=Clock::now();
   auto prepare_begin=Clock::now();auto prepared=pose::hdmi::prepare_background();auto prepare_end=Clock::now();
   auto* owned=prepared.rgb565.data();auto result=pose::hdmi::render(std::move(prepared),scores,poses,id,status);auto paint_end=Clock::now();
   need(result.rgb565.size()==4147200&&result.rgb565.data()==owned,"Prepared pixel ownership was copied or size changed");
   same(ordinary,result);
   if(status==pose_v1::render::Status::Result){
    std::vector<uint8_t> accepted(4147200);load(golden/("native-"+suffix+".rgb565"),accepted);
    need(accepted==result.rgb565,"Two-phase bytes differ from preserved accepted r47 native image");++golden_checks;
   }
   need(!std::memcmp(scores.data(),saved_scores.data(),sizeof(scores))&&
        !std::memcmp(poses.data(),saved_poses.data(),sizeof(poses)),"Renderer mutated model output arrays");
   preparation.push_back(elapsed(prepare_begin,prepare_end));dynamic.push_back(elapsed(prepare_end,paint_end));original.push_back(elapsed(begin,old_end));++checks;
  }
 }
 std::array<float,100> scores{};std::array<float,4200> poses{};bool rejected=false;
 try{pose::hdmi::render(pose::hdmi::PreparedBackground{},scores,poses,1);}catch(const std::exception&){rejected=true;}
 need(rejected,"Empty/unprepared pixel buffer accepted");
 scores[0]=std::numeric_limits<float>::quiet_NaN();rejected=false;
 try{pose::hdmi::render(pose::hdmi::prepare_background(),scores,poses,1);}catch(const std::exception&){rejected=true;}
 need(rejected,"NaN accepted after preparation");
 std::cout<<"{\"CPU_only\":true,\"SDK\":0,\"MMIO\":0,\"cases\":"<<checks<<",\"golden_checks\":"<<golden_checks
          <<",\"byte_parity\":true,\"model_values_preserved\":true,";
 stats("prepare_background",preparation);std::cout<<",";stats("dynamic_paint",dynamic);std::cout<<",";stats("original_render",original);std::cout<<"}\n";
 return 0;
}catch(const std::exception& error){std::cerr<<error.what()<<"\n";return 2;}}
