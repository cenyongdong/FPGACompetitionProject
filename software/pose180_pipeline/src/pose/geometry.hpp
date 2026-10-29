#pragma once
#include "postprocess.hpp"
#include <algorithm>
#include <cmath>

namespace pose::post::geometry {
using Centre=std::array<double,3>;
inline Centre centre(const Joints& p){Centre c{};for(unsigned j=0;j<14;++j)for(unsigned a=0;a<3;++a)c[a]+=p[3*j+a]/14.0;return c;}
inline double radius(const Joints& p,const Centre& c){double v=0;for(unsigned j=0;j<14;++j)for(unsigned a=0;a<3;++a)v+=std::pow(p[3*j+a]-c[a],2);return std::max(0.25,std::sqrt(v/14));}
inline double distance(const Centre& a,const Centre& b){double v=0;for(unsigned i=0;i<3;++i)v+=std::pow(a[i]-b[i],2);return std::sqrt(v);}
inline double shape(const Joints&a,const Centre&ac,const Joints&b,const Centre&bc){double v=0;for(unsigned i=0;i<42;++i)v+=std::pow((a[i]-ac[i%3])-(b[i]-bc[i%3]),2);return std::sqrt(v/14);}
}
