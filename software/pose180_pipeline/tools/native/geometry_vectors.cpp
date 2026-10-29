#include "fixed_geometry.hpp"
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
int main(int argc,char**argv){if(argc!=2)return 1;
 std::ofstream inputs(std::string(argv[1])+"/geometry_input.hex"),expected(std::string(argv[1])+"/geometry_expected.hex");
 inputs<<std::hex<<std::setfill('0');expected<<std::hex<<std::setfill('0');
 for(unsigned f=0;f<40;++f){std::array<std::int32_t,126>x{};
  for(unsigned p=0;p<3;++p)for(unsigned i=0;i<42;++i){double v=std::sin(i*.1+f*.1)*.5+(i%3==2?1.:0.);
   if(p)v+=(i%3==0?(f%10)*.07*p:0.);
   if(f%4==0&&p==2)v+=std::sin(i*.8)*.4;
   x[p*42+i]=std::int32_t(std::round(v*65536));}
  if(f==38)x.fill(1048576);if(f==39)x.fill(-1048576);
  unsigned mask=f%7+1;auto r=pose::geometry::evaluate(x,mask);
  for(auto v:x)inputs<<std::setw(8)<<std::uint32_t(v)<<'\n';
  expected<<std::setw(8)<<mask<<'\n'<<std::setw(8)<<r.duplicates<<'\n';
  for(auto&v:r.sums)for(auto q:v)expected<<std::setw(8)<<std::uint32_t(q)<<'\n';
  for(auto q:r.radius)expected<<std::setw(8)<<std::uint32_t(q)<<'\n'<<std::setw(8)<<std::uint32_t(q>>32)<<'\n';
 }
 std::cout<<"40 geometry vectors\n";
}
