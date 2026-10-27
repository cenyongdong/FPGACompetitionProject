#include "phase_branch.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace pose_v1 {
namespace {
constexpr double pi=3.141592653589793238462643383279502884;
void need(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
bool same(PhaseSampleIdentity a,PhaseSampleIdentity b){return a.epoch==b.epoch&&a.sample==b.sample&&a.time_ns==b.time_ns;}
}
PhaseBranchTracker::PhaseBranchTracker(std::int64_t max_gap_ns):max_gap_ns_(max_gap_ns) {
    need(max_gap_ns>0&&max_gap_ns<=1000000000,"Phase gap bound must be positive and at most one second");
}
void PhaseBranchTracker::reset(std::size_t r) {
    need(r<states_.size(),"Phase receiver out of range");auto& s=states_[r];
    s.have=false;s.previous={};s.winding={};s.cache.clear();++s.diagnostic.resets;
}
void PhaseBranchTracker::reset(){for(std::size_t r=0;r<3;++r)reset(r);}
PhaseBranchDiagnostic PhaseBranchTracker::diagnostics(std::size_t r)const {
    need(r<states_.size(),"Phase receiver out of range");return states_[r].diagnostic;
}
PhaseBranchHint PhaseBranchTracker::observe(std::size_t r,const std::array<std::complex<double>,3>& z,
                                           PhaseSampleIdentity id) {
    need(r<states_.size()&&id.epoch>0&&id.time_ns>=0,"Invalid phase source identity");
    for(auto v:z)need(std::isfinite(v.real())&&std::isfinite(v.imag()),"Non-finite phase reference");
    auto& s=states_[r];
    for(const auto& entry:s.cache)if(entry.id.epoch==id.epoch&&entry.id.sample==id.sample) {
        need(same(entry.id,id)&&entry.reference==z,"Phase sample identity reused with different data/time");
        auto hint=entry.hint;hint.reused=true;++s.diagnostic.reused;return hint;
    }
    if((s.have||!s.cache.empty())&&id.epoch==s.last.epoch)
        need(id.sample>s.last.sample&&id.time_ns>s.last.time_ns,"Unknown old phase sample; reset its source explicitly");
    PhaseBranchHint hint;
    auto reanchor=[&](){s.have=false;s.previous={};s.winding={};++s.diagnostic.resets;hint.reset=true;};
    if(!s.cache.empty()&&id.epoch!=s.last.epoch) {
        reset(r);hint.reset=true;
    }else if(s.have&&id.time_ns-s.last.time_ns>max_gap_ns_) {
        // An overlapping window can still reuse events before this gap. Keep
        // their immutable hints while reanchoring only the advancing state.
        reanchor();
    }
    // At a zero/deeply underflowed reference there is no defined phase branch.
    // Reanchor instead of forcing a correction inferred from undefined phase.
    bool defined=true;std::array<std::complex<double>,3> normalized;
    for(std::size_t a=0;a<3;++a) {
        const auto scale=std::max(std::abs(z[a].real()),std::abs(z[a].imag()));
        if(scale<1e-12)defined=false;
        else normalized[a]=z[a]/scale;
    }
    if(!defined) {
        reanchor();hint.defined=false;++s.diagnostic.undefined;
    }else {
        for(std::size_t p=0;p<2;++p) {
            const auto angle=std::arg(normalized[p+1]*std::conj(normalized[p]));
            if(s.have) {
                const auto step=angle-s.previous[p];
                if(step>pi){s.winding[p]=(s.winding[p]+2)%3;++s.diagnostic.branch_changes;}
                else if(step< -pi){s.winding[p]=(s.winding[p]+1)%3;++s.diagnostic.branch_changes;}
            }
            s.previous[p]=angle;
        }
        s.have=true;hint.rotation=std::uint8_t((2*s.winding[0]+s.winding[1])%3);
    }
    s.last=id;++s.diagnostic.samples;s.cache.push_back({id,z,hint});
    if(s.cache.size()>128)s.cache.pop_front();
    return hint;
}
Tokens apply_phase_branches(const Tokens& original,const PhaseHints& hints) {
    Tokens out=original;
    // Keep the original frequency unwrap/fit fixed. Assigning constant antenna
    // branches (0,q1,q1+q2)*2*pi leaves its LS slope unchanged; the common
    // intercept adds -2*pi*(2*q1+q2)/3. Integer antenna rotations vanish on
    // wrapping. Do not re-run frequency unwrap after adding large 2*pi offsets:
    // that can alter floating-point tie choices at exact +/-pi boundaries.
    for(std::size_t r=0;r<3;++r)for(std::size_t t=0;t<20;++t) {
        const auto rotation=hints[r][t];need(rotation<3,"Invalid phase branch rotation");
        if(!rotation)continue;
        const auto delta=-2*pi*double(rotation)/3;
        for(std::size_t a=0;a<3;++a)for(std::size_t n=0;n<30;++n) {
            const auto offset=((r*3+a)*20+t)*60;
            if(original[offset+n]==0)continue; // retain undefined zero-amplitude convention
            const auto angle=double(original[offset+30+n])+delta;
            out[offset+30+n]=float(std::atan2(std::sin(angle),std::cos(angle)));
        }
    }
    for(float v:out)need(std::isfinite(v),"Non-finite phase-corrected model input");
    return out;
}
} // namespace pose_v1
