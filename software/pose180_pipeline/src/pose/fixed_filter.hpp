#pragma once
#include <array>
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
namespace pose::post::fixed {
constexpr std::int32_t one=65536;
inline std::int32_t sat(std::int64_t x){return x>INT32_MAX?INT32_MAX:x<INT32_MIN?INT32_MIN:std::int32_t(x);}
inline std::int32_t q(double x){if(!std::isfinite(x))throw std::runtime_error("Nonfinite fixed input");return sat(std::llround(std::clamp(x,-32768.,32767.99998474121)*one));}
inline std::int32_t add(std::int32_t a,std::int32_t b){return sat(std::int64_t(a)+b);}
inline std::int32_t sub(std::int32_t a,std::int32_t b){return sat(std::int64_t(a)-b);}
inline std::int32_t mul(std::int32_t a,std::int32_t b){std::int64_t v=std::int64_t(a)*b;return sat(v<0?-((-v+32768)/one):(v+32768)/one);}
struct Parameters {std::int32_t inverse_dt,derivative_alpha,k,min_cutoff=one,beta=one/2;};
inline Parameters parameters(double dt){if(!(dt>=.001&&dt<=.25))throw std::runtime_error("Fixed dt outside supported range");double k=6.283185307179586*dt;return {q(1/dt),q(k/(1+k)),q(k)};}
struct State {std::int32_t x=0,y=0,d=0;};
inline std::int32_t step(State&s,std::int32_t x,const Parameters&p,bool init){
 if(init){s={x,x,0};return x;}
 auto v=mul(sub(x,s.x),p.inverse_dt);
 auto d=add(s.d,mul(p.derivative_alpha,sub(v,s.d)));
 auto absd=d==INT32_MIN?INT32_MAX:d<0?-d:d;
 auto cutoff=add(p.min_cutoff,mul(p.beta,absd));
 auto z=mul(p.k,cutoff);if(z<0)throw std::runtime_error("Invalid fixed cutoff");
 std::uint64_t den=std::uint64_t(z)+one;
 auto a=std::int32_t(((std::uint64_t(z)<<16)+den/2)/den);
 auto y=add(s.y,mul(a,sub(x,s.y)));s={x,y,d};return y;
}
}
