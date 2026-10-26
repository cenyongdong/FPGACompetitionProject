#include "receiver.hpp"
#include <cmath>
#include <iomanip>
#include <iostream>
using namespace pose::vitals;
int main(){
    constexpr double pi=3.14159265358979323846;ReceiverResampler receiver;
    std::cout<<std::setprecision(17);
    for(unsigned i=0;i<12600;++i){
        ReceiverSample raw;raw.session=1;raw.event_sequence=i+1;
        raw.time_ns=std::uint64_t(i)*1000000000/300+std::uint64_t(100000*(1+std::sin(i*.43)));
        const double t=raw.time_ns/1e9;std::cout<<"R,"<<raw.time_ns;
        for(unsigned ch=0;ch<4;++ch){const auto phase=.3*std::sin(2*pi*.25*t+ch*.1)+.03*std::sin(2*pi*1.2*t+ch*.2)+.002*std::sin(2*pi*91.2*t);
            raw.pairs[ch]={std::polar(1.,phase+3*std::sin(t)),std::polar(.8,3*std::sin(t))};std::cout<<','<<phase;
        }std::cout<<'\n';
        const auto res=receiver.push(raw);if(res.reset)return 1;
        for(const auto&sample:res.samples){std::cout<<"P,"<<sample.time_ns;for(auto p:sample.phase)std::cout<<','<<p;std::cout<<'\n';}
    }
}
