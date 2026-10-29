#include <algorithm>
#include "fixed_filter.hpp"
#include "postprocess.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
using namespace pose::post;
int main(int argc,char**argv){try{
 if(argc!=2)throw std::runtime_error("Expected vector output directory");std::string root=argv[1];
 std::ofstream input(root+"/input.hex"),expected(root+"/expected.hex"),params(root+"/params.hex");if(!input||!expected||!params)throw std::runtime_error("Cannot create vectors");
 input<<std::hex;expected<<std::hex;params<<std::hex;
 std::array<fixed::State,126> state{};std::array<OneEuro,126> floats{};double max_error=0;
 for(unsigned f=0;f<40;++f){double dt=f%3==0?.061:f%3==1?.067:.11;auto p=fixed::parameters(dt);unsigned mask=f==0?7:f==12?2:0,update=f>=24&&f<32?1u<<(f%3):7;
  for(auto v:{p.inverse_dt,p.derivative_alpha,p.k,p.min_cutoff,p.beta,std::int32_t(mask),std::int32_t(update)})params<<std::uint32_t(v)<<'\n';
  for(unsigned i=0;i<126;++i){double x=f>=32?((f+i)%2?32767.999:-32768.):2+.3*std::sin(double(f)*.2+i*.07);bool init=(mask>>(i/42))&1;auto value=fixed::q(x);auto y=(update>>(i/42))&1?fixed::step(state[i],value,p,init):state[i].y;
   if(init)floats[i].reset();if(f<24){double reference=floats[i].update(double(value)/65536,dt,{});max_error=std::max(max_error,std::abs(double(y)/65536-reference));}
   input<<std::uint32_t(value)<<'\n';expected<<std::uint32_t(y)<<'\n';}
 }
 if(max_error>.001)throw std::runtime_error("Fixed/float tolerance exceeded");
 std::cout<<"{\"frames\":40,\"coordinates\":126,\"max_fixed_float_error\":"<<max_error<<"}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
