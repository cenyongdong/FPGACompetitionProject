#include "reference.hpp"
#include "stream.hpp"
#include "pl_acf.hpp"
#include "receiver.hpp"
#include <algorithm>
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <map>

using namespace pose::vitals;
namespace {
constexpr double pi=3.14159265358979323846;
void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
template<class F>void rejects(F f){bool threw=false;try{f();}catch(const std::exception&){threw=true;}need(threw,"Expected rejection");}
PhaseSample sample(unsigned i,double heart=1.2){PhaseSample s;s.time_ns=std::uint64_t(i)*20000000;s.sequence=i+1;s.source_support_valid=true;
    for(unsigned ch=0;ch<4;++ch)s.phase[ch]=.3*std::sin(2*pi*.25*i/50+ch*.1)+.03*std::sin(2*pi*heart*i/50+ch*.2);return s;}
PhaseWindow window(PhaseClock clock=PhaseClock::Synthetic){PhaseWindow w;w.clock=clock;w.clock_evidence="unit test synthetic";for(unsigned i=0;i<2000;++i)w.samples.push_back(sample(i));return w;}
struct RegisterModel {
    std::map<unsigned,std::uint32_t> regs;std::vector<std::int32_t> input;std::vector<std::int64_t> result;bool hang=false;
    unsigned reads=0,writes=0;
    std::uint32_t read(unsigned a){++reads;if(a==0)return 0x56414301;if(a==0x24)return input.size();
        if(a==0x2c)return std::uint32_t(result.at(regs[0x28]));if(a==0x30)return std::uint32_t(result.at(regs[0x28])>>32);return regs[a];}
    void write(unsigned a,std::uint32_t v){++writes;
        if(a==0x20)input.push_back(std::int32_t(v));
        else if(a==8&&v==2){regs.clear();input.clear();result.clear();}
        else if(a==8&&v==1){regs[4]=hang?1:2;regs[0x18]=hang?0:regs[0x14];if(!hang){ScalarDots s;result=s.calculate(input,regs[0x10]);}}
        else regs[a]=v;
    }
};
}
int main(){try{
    unsigned passed=0;auto test=[&](const char*name,auto f){f();++passed;std::cout<<"PASS "<<name<<'\n';};
    ScalarDots dots;FixedCorrelation fixed(dots);
    test("float_fixed_correlation",[&]{std::mt19937 rng(41);std::uniform_real_distribution<double>d(-1,1);double maximum=0;
        for(unsigned n:{32u,129u,1500u,2048u}){std::vector<double>x(n);for(auto&v:x)v=d(rng);const auto lag=std::min<std::size_t>(511,n-1);
            const auto a=floating_correlation(x,lag),b=fixed.correlate(x,lag);for(unsigned k=0;k<a.size();++k)maximum=std::max(maximum,std::abs(a[k]-b[k]));}
        need(maximum<.0001,"Quantization error");std::cout<<"max_acf_difference="<<maximum<<'\n';});
    test("fixed_limits_zero_and_small",[&]{need(dots.calculate(std::vector<std::int32_t>(2048,65535),511)[0]==std::int64_t(2048)*65535*65535,"Accumulator bound");
        rejects([&]{dots.calculate({65536,0},1);});rejects([&]{dots.calculate(std::vector<std::int32_t>(2048),512);});
        auto z=fixed.correlate(std::vector<double>(100,0),50);need(z[0]==0,"Zero energy");
        z=fixed.correlate(std::vector<double>(100,1e-20),50);need(z[0]==0,"Tiny physical energy");});
    test("phase_and_original_pipeline",[&]{auto p=window();Window iq;iq.clock=ClockKind::SyntheticUniform;
        for(const auto&x:p.samples){Sample s;s.time_ns=x.time_ns;s.sequence=x.sequence;for(unsigned c=0;c<4;++c)s.pairs[c]={std::polar(1.,x.phase[c]),{1,0}};iq.samples.push_back(s);}
        const auto a=analyze(iq),b=analyze_phase(p),c=analyze_phase(p,{},&fixed);
        need(a.heart&&b.heart&&c.heart,"Missing HR");need(std::abs(a.heart->bpm-b.heart->bpm)<1e-8,"Shared math changed");
        need(std::abs(b.heart->bpm-c.heart->bpm)<.01,"Fixed HR differs");need(std::abs(c.heart->bpm-72)<1,"Heart rate");});
    test("phase_provenance_and_faults",[&]{auto p=window(PhaseClock::RelativeRx);need(analyze_phase(p).status=="candidate_unverified","Derived clock promoted");
        p.clock=PhaseClock::Unknown;need(!analyze_phase(p).heart,"Unknown clock");p=window();p.samples[1100].source_support_valid=false;need(!analyze_phase(p).heart,"Invalid FIR footprint");
        p=window();p.samples[1100].phase[0]+=1;auto isolated=analyze_phase(p);need(isolated.heart&&isolated.heart->agreeing_channels==3&&!isolated.trace[0].heart_candidate.usable,"Bad channel participated");
        p.samples[1100].phase[1]+=1;need(!analyze_phase(p).heart,"Two bad channels accepted");});
    test("bounded_stream_gap_recovery",[&]{PhaseStream stream(PhaseClock::Synthetic,"synthetic",{},&fixed);StreamUpdate u;unsigned outputs=0;
        for(unsigned i=0;i<2200;++i){u=stream.push(1,sample(i));outputs+=bool(u.result.heart);need(stream.buffered()<=2000,"Unbounded ring");}
        need(outputs==5,"One-second stride");auto bad=sample(2200);bad.source_support_valid=false;u=stream.push(1,bad);need(!u.result.heart&&u.buffered==0,"Stale after fault");
        for(unsigned i=2201;i<=4200;++i)u=stream.push(1,sample(i));need(u.result.heart.has_value(),"No recovery");u=stream.push(2,sample(4201));need(!u.result.heart&&u.buffered==1,"Mixed session");});
    test("raw_receiver_antialias_heart_and_recovery",[&]{ReceiverStream receiver(PhaseClock::Synthetic,"generated 300Hz raw pairs",&fixed);unsigned estimates=0;ReceiverSample raw;
        for(unsigned i=0;i<12600;++i){raw={};raw.session=9;raw.time_ns=std::uint64_t(i)*1000000000/300;raw.event_sequence=i+1;
            const double t=double(i)/300;for(unsigned ch=0;ch<4;++ch){double p=.3*std::sin(2*pi*.25*t+ch*.1)+.03*std::sin(2*pi*1.2*t+ch*.2)+.002*std::sin(2*pi*91.2*t);
                raw.pairs[ch]={std::polar(1.,p+3*std::sin(t)),std::polar(.8,3*std::sin(t))};}
            for(const auto&u:receiver.push(raw))if(u.result.heart){++estimates;need(std::abs(u.result.heart->bpm-72)<1,"Raw stream rate");}
        }need(estimates==2,"Raw stream cadence/context");
        const auto expired=receiver.invalidate("idle_deadline");need(expired.buffered==0&&!expired.result.heart&&expired.result.status=="source_unavailable","Silence retained HR");
        receiver.push(raw);raw.time_ns+=20000000;++raw.event_sequence;const auto u=receiver.push(raw);need(!u.empty()&&!u[0].result.heart&&u[0].buffered==0,"Raw gap retained HR");});
    test("pl_identity_and_transport",[&]{RegisterModel m;auto rd=[&](unsigned a){return m.read(a);};auto wr=[&](unsigned a,unsigned v){m.write(a,v);};
        rejects([&]{PlDotProducts p("r45",true,rd,wr);});rejects([&]{PlDotProducts p("vitals-acf-v1",false,rd,wr);});need(!m.reads&&!m.writes,"Unqualified MMIO");
        PlDotProducts p("vitals-acf-v1",true,rd,wr);std::vector<std::int32_t>x={-65535,65535,3,-9,12};need(p.calculate(x,4)==dots.calculate(x,4),"Register results");
        need(p.calculate(x,2)==dots.calculate(x,2),"Second sequence");});
    test("raw_channel_fault_isolation",[&]{
        for(unsigned damaged:{1u,2u}){ReceiverStream receiver(PhaseClock::Synthetic,"channel fault injection");unsigned estimates=0;
            for(unsigned i=0;i<12600;++i){ReceiverSample raw;raw.session=1;raw.event_sequence=i+1;raw.time_ns=std::uint64_t(i)*1000000000/300;
                double t=double(i)/300;for(unsigned c=0;c<4;++c){double phase=.3*std::sin(2*pi*.25*t+c*.1)+.03*std::sin(2*pi*1.2*t+c*.2);
                    if(i>=3000&&c<damaged)phase+=1;raw.pairs[c]={std::polar(1.,phase),{1,0}};}
                for(const auto&u:receiver.push(raw))if(u.result.heart){++estimates;need(u.result.heart->agreeing_channels==3,"Damaged raw feature voted");}
            }need(estimates==(damaged==1?2u:0u),"Fault isolation/consensus weakened");
        }
    });
    test("pl_timeout_isolates",[&]{RegisterModel m;m.hang=true;PlDotProducts p("vitals-acf-v1",true,[&](unsigned a){return m.read(a);},[&](unsigned a,unsigned v){m.write(a,v);},std::chrono::milliseconds(1));
        rejects([&]{p.calculate({1,2,3},1);});auto calls=m.reads+m.writes;rejects([&]{p.calculate({1,2,3},1);});need(calls==m.reads+m.writes,"Retried isolated device");});
    test("pl_timeout_cpu_continuation",[&]{RegisterModel m;m.hang=true;PlDotProducts p("vitals-acf-v1",true,[&](unsigned a){return m.read(a);},[&](unsigned a,unsigned v){m.write(a,v);},std::chrono::milliseconds(1));
        FixedCorrelation accelerated(p);FallbackCorrelation fallback(accelerated);
        auto r=analyze_phase(window(),{},&fallback);need(r.heart&&std::abs(r.heart->bpm-72)<1&&!fallback.fault().empty(),"CPU fallback failed");
        need(r.correlation_backend=="float64_cpu_after_backend_fault","Backend fault hidden");auto calls=m.reads+m.writes;
        r=analyze_phase(window(),{},&fallback);need(r.heart&&calls==m.reads+m.writes,"Fallback retried hardware");});
    std::cout<<"hybrid_passed="<<passed<<'\n';return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
