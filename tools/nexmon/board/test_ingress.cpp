#include "ingress.hpp"
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <vector>

using namespace nexmon_board;
namespace {
void check(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}
void throws(const std::function<void()>&f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}check(caught,"Expected rejection");}
void put(std::vector<std::uint8_t>&b,std::size_t at,std::uint64_t v,std::size_t n){for(std::size_t i=0;i<n;++i)b[at+i]=std::uint8_t(v>>(8*i));}
Config config(){Config c;c.session_id="test-job";c.receiver_ids={"one","two","three"};c.transmitter_mac={2,17,34,51,68,85};c.chanspec=0xd0a1;c.expected_events=800;c.gains={1,2,3};return c;}
struct Source {
    std::size_t counter[3]{};
    void event(Ingress&in,std::size_t r,int ordinal,int origin=0,int clock_offset=0,
               bool retry=false,int cores=3,bool lose_diag=false,int seq_override=-1,int offset_us=0) {
        auto c=config();auto timestamp=std::int64_t(std::llround(double(ordinal)*1000000/300))+clock_offset+offset_us;
        auto arrival=100000000+std::int64_t(std::llround(double(ordinal)*1000000/300))+offset_us;
        auto seq=seq_override>=0?seq_override:((ordinal+origin)&4095)<<4;
        for(int core=0;core<cores;++core) {
            std::vector<std::uint8_t>b(274),d(50);put(b,0,0x1111,2);std::copy(c.transmitter_mac.begin(),c.transmitter_mac.end(),b.begin()+4);
            put(b,10,std::uint64_t(seq),2);put(b,12,std::uint64_t(core<<8),2);put(b,14,c.chanspec,2);put(b,16,106,2);
            for(int i=0;i<64;++i)put(b,18+std::size_t(i)*4,std::uint64_t((i+1)<<18),4);
            std::memcpy(d.data(),"NMD3",4);put(d,4,3,2);put(d,6,50,2);std::copy(c.transmitter_mac.begin(),c.transmitter_mac.end(),d.begin()+8);
            put(d,14,std::uint64_t(seq),2);put(d,16,std::uint64_t(core<<8),2);put(d,18,c.chanspec,2);put(d,20,8|(retry?0x800:0),2);put(d,22,0xaaaa,2);put(d,24,std::uint64_t(timestamp),2);put(d,26,counter[r],2);
            put(d,28,28,2);put(d,30,3,2);for(int i=0;i<3;++i)put(d,32+std::size_t(i)*4,std::uint64_t((100+i)<<18),4);put(d,44,59,2);put(d,46,std::uint64_t(timestamp+80),4);
            in.feed(r,c.session_id,arrival+core,5500,b.data(),b.size());
            if(!lose_diag)in.feed(r,c.session_id,arrival+core,5501,d.data(),d.size());
        }
        ++counter[r];
    }
};
BatchResult run(int origin=0,int drop=-1,bool retry=false,bool partial_tail=false) {
    Ingress in(config());Source source;std::size_t emitted=0;bool before_eof=false;
    for(int ordinal=0;ordinal<800;++ordinal)for(std::size_t r=0;r<3;++r) {
        if(r==1&&ordinal==drop)continue;
        source.event(in,r,ordinal,origin,int(r)*12345,false,partial_tail&&ordinal==799&&r==2?2:3);
        if(retry&&r==1&&ordinal==410)source.event(in,r,ordinal,origin,int(r)*12345,true,3,false,-1,400);
        auto ready=in.take_ready();emitted+=ready.size();if(!ready.empty()&&ordinal<799)before_eof=true;
    }
    auto result=in.finish();check(before_eof,"No output before EOF");check(emitted==result.windows.size(),"Incremental/final window mismatch");
    throws([&]{in.finish();});return result;
}
}
int main() {
    int passed=0;
    try {
        auto baseline=run();check(!baseline.windows.empty()&&baseline.windows.size()==baseline.decisions.size(),"Uniform data rejected");++passed;
        auto missing=run(0,410);check(missing.windows.size()+1==missing.decisions.size(),"Missing event did not reject one whole window");++passed;
        auto rollover=run(4000);for(const auto&n:rollover.nodes)check(n.wraps==1,"Safe modulo4096 rollover not retained");++passed;
        auto retry=run(0,-1,true);check(retry.nodes[1].retransmissions==1&&retry.windows.size()==baseline.windows.size(),"Retry did not preserve first valid");++passed;
        auto partial=run(0,-1,false,true);check(partial.nodes[2].trailing_cores==2,"Unfinished core tail not retained in diagnostic");++passed;
        auto c=config();c.gains[1]=0;throws([&]{Ingress bad(c);});c.gains[1]=std::numeric_limits<double>::quiet_NaN();throws([&]{Ingress bad(c);});++passed;
        {Ingress in(config());std::uint8_t b=0;throws([&]{in.feed(0,"another-job",0,5500,&b,1);});Source s;throws([&]{s.event(in,0,0);});}++passed;
        {Ingress in(config());std::uint8_t b=0;throws([&]{in.feed(0,"test-job",0,5500,&b,1);});}++passed;
        {Ingress in(config());Source s;s.event(in,0,0,0,0,false,2);throws([&]{s.event(in,0,1);});}++passed;
        {Ingress in(config());Source s;s.event(in,0,0,0,0,false,1,true);throws([&]{s.event(in,0,1);});}++passed;
        {Ingress in(config());Source s;s.event(in,0,0);throws([&]{s.event(in,0,1,0,0,false,3,false,0);});}++passed;
        {Ingress in(config());Source s;s.event(in,0,0);throws([&]{s.event(in,0,1,0,0,false,3,false,2048<<4);});}++passed;
        {Ingress in(config());Source s;s.event(in,0,0);throws([&]{in.expire(0,100032770);});}++passed;
        {auto w=baseline.windows.front();auto b=encode_piwcsi2(w,42,123);check(b.size()==86432&&std::memcmp(b.data(),"PIWCSI2\0",8)==0,"Protocol header changed");check(b[8]==2&&b[16]==42&&b[24]==123,"Protocol fields changed");w.csi[0]={std::numeric_limits<double>::infinity(),0};throws([&]{encode_piwcsi2(w,0,0);});}++passed;
        {auto z=decode_acphy((17u<<18)|(9u<<6)|(1u<<29)|(1u<<17)|63u);check(z==std::complex<double>(-8.5,-4.5),"Signed mantissa/exponent decode changed");}++passed;
        std::cout<<"ingress directed checks passed="<<passed<<'\n';return 0;
    }catch(const std::exception&e){std::cerr<<"directed ingress failure after "<<passed<<" checks: "<<e.what()<<'\n';return 1;}
}
