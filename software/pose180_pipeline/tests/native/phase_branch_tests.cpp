#include "software/core/input/phase_branch.hpp"
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>

using namespace pose_v1;
namespace {
constexpr double pi=3.141592653589793238462643383279502884;
void need(bool v,const char* s){if(!v)throw std::runtime_error(s);}
void rejects(const std::function<void()>& f){bool caught=false;try{f();}catch(const std::exception&){caught=true;}need(caught,"Expected rejection");}
std::array<std::complex<double>,3> reference(int sample) {
    return {std::polar(1.0,0.0),std::polar(1.0,pi-.005+.01*(sample>=10)),std::polar(1.0,pi+.195+.01*(sample>=10))};
}
RawCsi fixture(int kind) {
    RawCsi raw;
    for(std::size_t r=0;r<3;++r)for(std::size_t a=0;a<3;++a)for(std::size_t n=0;n<30;++n)for(std::size_t t=0;t<20;++t) {
        double phase=.04*double(n)+.4*double(a);
        if(kind==1)phase+=1.2*double(t>=10);
        if(kind==2)phase+=1.2*double(t>=10&&a==2);
        if(kind==3)phase=.04*double(n)+(a?pi-.005+.01*double(t>=10)+.2*double(a==2):0);
        raw[raw_index(r,a,n,t)]=std::polar(1.0,phase);
    }return raw;
}
PhaseHints track(PhaseBranchTracker& tracker,const RawCsi& raw) {
    PhaseHints hints{};
    for(std::size_t r=0;r<3;++r)for(std::size_t t=0;t<20;++t) {
        std::array<std::complex<double>,3> z;
        for(std::size_t a=0;a<3;++a)z[a]=raw[raw_index(r,a,0,t)];
        hints[r][t]=tracker.observe(r,z,{1,t,std::int64_t(t)*3333333}).rotation;
    }return hints;
}
double step(const Tokens& tokens,std::size_t a=0) {
    const auto before=(a*20+9)*60+30,after=(a*20+10)*60+30;
    return std::abs(std::remainder(double(tokens[after])-tokens[before],2*pi));
}
}
int main() {
    int cases=0;
    try {
        for(int kind:{0,1,2}) {
            auto raw=fixture(kind);PhaseBranchTracker tracker;auto original=preprocess(raw);
            auto corrected=apply_phase_branches(original,track(tracker,raw));
            need(std::memcmp(original.data(),corrected.data(),sizeof(original))==0,"Unchanged branches altered original tokens");
            if(kind==2)need(step(corrected,2)>.79,"Actual antenna phase step was erased");
            ++cases;
        }
        {
            auto raw=fixture(3);PhaseBranchTracker tracker;auto original=preprocess(raw);
            auto corrected=apply_phase_branches(original,track(tracker,raw));
            need(step(original)>2&&step(corrected)<.007,"Smooth pi crossing not corrected");
            for(std::size_t i=0;i<corrected.size();++i)if(i%60<30)need(std::memcmp(&corrected[i],&original[i],4)==0,"Amplitude changed");
            for(std::size_t t=0;t<20;++t)for(std::size_t n=0;n<30;++n) {
                const auto a=t*60+30+n,b=(20+t)*60+30+n;
                need(std::abs(std::remainder(double(corrected[a])-corrected[b]-double(original[a])+original[b],2*pi))<1e-6,"Wrapped antenna difference changed");
            }++cases;
        }
        {
            PhaseBranchTracker tracker;std::array<std::uint8_t,30> hints{};
            for(std::size_t n=0;n<20;++n)hints[n]=tracker.observe(0,reference(int(n)),{1,n,std::int64_t(n)*3333333}).rotation;
            for(std::size_t n=10;n<30;++n) {
                auto h=tracker.observe(0,reference(int(n)),{1,n,std::int64_t(n)*3333333});
                if(n<20)need(h.reused&&h.rotation==hints[n],"Overlapping window advanced/reinterpreted state");
            }
            need(tracker.diagnostics(0).samples==30&&tracker.diagnostics(0).reused==10,"Unexpected state advancement");
            auto changed=reference(12);changed[0]={2,0};rejects([&]{tracker.observe(0,changed,{1,12,39999996});});++cases;
        }
        {
            PhaseBranchTracker tracker;
            for(std::size_t n=0;n<1000;++n) {
                const double p1=.05*double(n),p2=.09*double(n);
                std::array<std::complex<double>,3> z{std::polar(1.0,0.0),std::polar(1.0,p1),std::polar(1.0,p1+p2)};
                const auto h=tracker.observe(0,z,{1,n,std::int64_t(n)*3333333});
                const int q1=int(std::floor((p1+pi)/(2*pi))),q2=int(std::floor((p2+pi)/(2*pi)));
                need(h.rotation==(2*q1+q2)%3,"Many-winding modulo state differs from unbounded phase");
            }++cases;
        }
        {
            PhaseBranchTracker tracker;std::array<PhaseBranchHint,20> original{};
            for(std::size_t n=0;n<20;++n) {
                auto z=reference(int(n));if(n==15)z[0]={0,0};
                original[n]=tracker.observe(0,z,{1,n,std::int64_t(n)*3333333+(n>=12?20000000:0)});
            }
            for(std::size_t n=10;n<20;++n) {
                auto z=reference(int(n));if(n==15)z[0]={0,0};
                const auto h=tracker.observe(0,z,{1,n,std::int64_t(n)*3333333+(n>=12?20000000:0)});
                need(h.reused&&h.rotation==original[n].rotation&&h.defined==original[n].defined,"Overlap across reanchor lost immutable event hints");
            }++cases;
        }
        {
            PhaseBranchTracker tracker;
            for(std::size_t n=0;n<20;++n)tracker.observe(0,reference(int(n)),{1,n,std::int64_t(n)*3333333});
            auto gap=tracker.observe(0,reference(20),{1,20,100000000});need(gap.reset&&gap.rotation==0,"Gap did not reanchor");
            auto epoch=tracker.observe(0,reference(0),{2,0,0});need(epoch.reset&&epoch.rotation==0,"Epoch did not reanchor");
            auto zero=tracker.observe(0,{{{0,0},{1,0},{1,0}}},{2,1,3333333});need(!zero.defined&&zero.rotation==0,"Undefined phase corrected");++cases;
        }
        {
            PhaseBranchTracker tracker;
            for(std::size_t n=0;n<1000;++n)tracker.observe(0,reference(int(n)),{1,n,std::int64_t(n)*3333333});
            rejects([&]{tracker.observe(0,reference(1),{1,1,3333333});});
            tracker.reset();need(tracker.observe(0,reference(0),{2,0,0}).rotation==0,"Explicit reset failed");
            PhaseHints bad{};bad[0][0]=3;rejects([&]{apply_phase_branches(preprocess(fixture(0)),bad);});++cases;
        }
        std::cout<<"phase branch cases passed="<<cases<<"; no SDK; original preprocessing preserved\n";return 0;
    }catch(const std::exception& e){std::cerr<<"phase branch cases passed="<<cases<<" failed: "<<e.what()<<'\n';return 1;}
}
