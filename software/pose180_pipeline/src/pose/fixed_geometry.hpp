#pragma once
#include <array>
#include <algorithm>
#include <cstdint>
#include <stdexcept>
namespace pose::geometry {
// Q16.16 coordinates, bounded to +/-16 model units. Integer moments preserve
// all fractional bits; no square root is required by the duplicate decision.
struct Result {
 std::array<std::array<std::int32_t,3>,3> sums{};
 std::array<std::uint64_t,3> radius{}; // 196 * RMS-radius^2 in Q32
 unsigned duplicates=0; // pairs (0,1), (0,2), (1,2)
};
constexpr std::uint64_t radius_floor=52613349376ull;
inline Result evaluate(const std::array<std::int32_t,126>& x,unsigned mask){
 Result r;
 for(unsigned s=0;s<3;++s){r.radius[s]=radius_floor;if(!(mask&(1u<<s)))continue;
  std::uint64_t q=0;for(unsigned i=0;i<42;++i){std::int64_t v=x[42*s+i];if(v< -1048576||v>1048576)throw std::runtime_error("Geometry range exceeded");r.sums[s][i%3]+=std::int32_t(v);q+=std::uint64_t(v*v);}
  std::uint64_t c=0;for(auto v:r.sums[s])c+=std::uint64_t(std::int64_t(v)*v);
  r.radius[s]=std::max(radius_floor,14*q-c);
 }
 unsigned bit=0;for(unsigned a=0;a<3;++a)for(unsigned b=a+1;b<3;++b,++bit){
  if((mask&((1u<<a)|(1u<<b)))!=((1u<<a)|(1u<<b)))continue;
  std::uint64_t full=0,centre=0;for(unsigned i=0;i<42;++i){const std::int64_t d=std::int64_t(x[42*a+i])-x[42*b+i];full+=std::uint64_t(d*d);}
  for(unsigned k=0;k<3;++k){const std::int64_t d=std::int64_t(r.sums[a][k])-r.sums[b][k];centre+=std::uint64_t(d*d);}
  full*=14;const auto shape=full-centre,scale=std::max(r.radius[a],r.radius[b]);
  // Exact rational forms of the default .3/.3 and .7/.2 thresholds.
  if((100*centre<9*scale&&100*full<9*scale)||(100*centre<49*scale&&25*shape<scale))r.duplicates|=1u<<bit;
 }
 return r;
}
}
