// CPU-only kernel benchmark: no SDK, device access, input transport or rendering.
#include "postprocess.hpp"
#include "fixed_filter.hpp"
#include <algorithm>
#include <array>
#include <chrono>
#include <cmath>
#include <iostream>
#include <numeric>
#include <vector>
using namespace pose::post;
using Clock=std::chrono::steady_clock;
int main(){
 constexpr unsigned warmup=256, measured=10000;
 std::array<std::array<float,126>,64> input{};
 std::array<std::array<std::int32_t,126>,64> quantized{};
 for(unsigned f=0;f<64;++f)for(unsigned i=0;i<126;++i){
  input[f][i]=float(.2*std::sin(.1*f+.03*i)+.002*i);
  quantized[f][i]=fixed::q(input[f][i]);
 }
 auto emit=[](const char*name,unsigned coordinates,std::vector<double> ns,double checksum){
  const double mean=std::accumulate(ns.begin(),ns.end(),0.)/ns.size();
  std::sort(ns.begin(),ns.end());
  std::cout<<"{\"kernel\":\""<<name<<"\",\"coordinates\":"<<coordinates
   <<",\"samples\":"<<ns.size()<<",\"warmup\":256,\"mean_us\":"<<mean/1000
   <<",\"p50_us\":"<<ns[ns.size()/2]/1000<<",\"p95_us\":"<<ns[ns.size()*95/100]/1000
   <<",\"max_us\":"<<ns.back()/1000<<",\"checksum\":"<<checksum<<"}\n";
 };
 for(unsigned coordinates:{42u,126u})for(bool fixed_mode:{false,true}){
  std::array<OneEuro,126> floating{};std::array<fixed::State,126> integer{};
  std::array<double,126> output{};std::vector<double> samples;samples.reserve(measured);
  Config config;double checksum=0;
  for(unsigned f=0;f<warmup+measured;++f){
   const auto&x=input[f%64];const auto&q=quantized[f%64];
   const double dt=(f%3==0?.067:f%3==1?.11:.061);
   // Parameter conversion is also needed on PS before a PL submission. Include
   // it in the fixed CPU kernel; pre-quantized input conversion is excluded.
   auto begin=Clock::now();
   if(fixed_mode){const auto p=fixed::parameters(dt);for(unsigned i=0;i<coordinates;++i)output[i]=fixed::step(integer[i],q[i],p,f==0);}
   else for(unsigned i=0;i<coordinates;++i)output[i]=floating[i].update(x[i],dt,config);
   auto end=Clock::now();
   if(f>=warmup)samples.push_back(std::chrono::duration<double,std::nano>(end-begin).count());
   for(unsigned i=0;i<coordinates;++i)checksum+=output[i];
  }
  emit(fixed_mode?"q16_cpu":"float_cpu",coordinates,samples,checksum);
 }
 std::vector<double> overhead;overhead.reserve(measured);
 for(unsigned f=0;f<measured;++f){auto a=Clock::now();auto b=Clock::now();overhead.push_back(std::chrono::duration<double,std::nano>(b-a).count());}
 emit("clock_pair",0,overhead,0);
}
