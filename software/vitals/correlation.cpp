#include "correlation.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace pose::vitals {
std::vector<double> floating_correlation(const std::vector<double>& x,std::size_t last) {
    if(x.empty()||last>=x.size())throw std::invalid_argument("ACF lag outside input");
    std::vector<double> output(last+1);
    for(std::size_t k=0;k<=last;++k){
        double product=0,first=0,second=0;
        for(std::size_t i=k;i<x.size();++i){
            product+=x[i]*x[i-k];first+=x[i]*x[i];second+=x[i-k]*x[i-k];
        }
        const auto norm=std::sqrt(first)*std::sqrt(second);
        output[k]=norm>1e-24?product/norm:0;
    }
    return output;
}
void validate_dot_input(const std::vector<std::int32_t>& x,std::size_t last){
    if(x.empty()||x.size()>acf_max_samples||last>acf_max_lag||last>=x.size())
        throw std::invalid_argument("Fixed ACF capacity/lag");
    for(auto v:x)if(v < -acf_peak||v>acf_peak)throw std::invalid_argument("Fixed ACF sample range");
}
std::vector<std::int64_t> ScalarDots::calculate(const std::vector<std::int32_t>& x,std::size_t last){
    validate_dot_input(x,last);std::vector<std::int64_t> out(last+1);
    for(std::size_t k=0;k<=last;++k)for(std::size_t i=k;i<x.size();++i)
        out[k]+=std::int64_t(x[i])*x[i-k];
    return out;
}
std::vector<double> FixedCorrelation::correlate(const std::vector<double>& x,std::size_t last){
    if(x.empty()||x.size()>acf_max_samples||last>acf_max_lag||last>=x.size())
        throw std::invalid_argument("Fixed ACF capacity/lag");
    double peak=0;for(auto v:x){if(!std::isfinite(v))throw std::invalid_argument("Nonfinite ACF input");peak=std::max(peak,std::abs(v));}
    if(peak==0)return std::vector<double>(last+1,0);
    std::vector<std::int32_t> q;std::vector<std::int64_t> energy(1,0);q.reserve(x.size());energy.reserve(x.size()+1);
    for(auto v:x){const auto value=std::int32_t(std::llround((v/peak)*acf_peak));q.push_back(value);energy.push_back(energy.back()+std::int64_t(value)*value);}
    const auto sums=dots_.calculate(q,last);
    if(sums.size()!=last+1)throw std::runtime_error("ACF incomplete result");
    std::vector<double> out(last+1);
    for(std::size_t k=0;k<=last;++k){
        const auto a=energy.back()-energy[k],b=energy[x.size()-k];
        const auto norm=std::sqrt(double(a))*std::sqrt(double(b));
        // Check the exact integer result, not merely an arbitrary finite value.
        // N <= 2048, |q| <= 65535 -> dot/energy < 2^43, safely inside 48 bits.
        if(std::abs(double(sums[k]))>norm+1.0||(k==0&&sums[k]!=energy.back()))
            throw std::runtime_error("ACF result violates energy bound");
        const auto physical_norm=(norm/acf_peak)*peak/acf_peak*peak;
        out[k]=physical_norm>1e-24&&norm>0?double(sums[k])/norm:0;
    }
    return out;
}
std::vector<double> FallbackCorrelation::correlate(const std::vector<double>& x,std::size_t last){
    if(!isolated_)try{return primary_.correlate(x,last);}
    catch(const std::exception& error){fault_=error.what();isolated_=true;}
    return floating_correlation(x,last);
}
}
