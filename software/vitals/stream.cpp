#include "stream.hpp"
#include <cmath>
#include <stdexcept>

namespace pose::vitals {
PhaseStream::PhaseStream(PhaseClock clock,std::string evidence,Config c,CorrelationBackend* backend)
 :config_(c),clock_(clock),evidence_(std::move(evidence)),backend_(backend){
    // Reuse complete configuration validation without running a workload.
    PhaseWindow empty;empty.clock=clock_;empty.clock_evidence=evidence_;analyze_phase(empty,c);
    needed_=std::size_t(std::llround((c.warmup_seconds+c.window_seconds)*c.sample_rate));
    stride_=std::max<std::size_t>(1,std::size_t(std::llround(c.sample_rate)));
    if(evidence_.empty()||(clock_!=PhaseClock::Synthetic&&clock_!=PhaseClock::RelativeRx&&clock_!=PhaseClock::VerifiedSampling))throw std::invalid_argument("Phase stream needs explicit provenance");
}
StreamUpdate PhaseStream::invalidate(const std::string& reason){
    StreamUpdate out;out.session=session_;
    if(!ring_.empty()){out.sequence=ring_.back().sequence;out.first_ns=ring_.front().time_ns;out.last_ns=ring_.back().time_ns;}
    ring_.clear();since_=0;out.resets=++resets_;
    out.result.status="source_unavailable";out.result.reasons={reason};return out;
}
StreamUpdate PhaseStream::push(std::uint64_t session,const PhaseSample& x){
    if(!session)throw std::invalid_argument("Nonzero vitals session required");
    StreamUpdate out;out.session=session;out.sequence=x.sequence;out.last_ns=x.time_ns;
    PhaseSample current=x;bool bad=!x.source_support_valid;
    for(std::size_t ch=0;ch<channels;++ch)if(!std::isfinite(x.phase[ch]))current.channel_valid[ch]=false;
    bool discontinuity=session_&&session_!=session;
    if(!ring_.empty()&&!discontinuity){const auto& p=ring_.back();
        discontinuity=x.time_ns<=p.time_ns||x.sequence<=p.sequence||x.sequence-p.sequence!=1;
        if(x.time_ns>p.time_ns)discontinuity|=std::abs((x.time_ns-p.time_ns)/1e6-1000/config_.sample_rate)>config_.max_jitter_ms;
        for(std::size_t c=0;c<channels;++c)if(current.channel_valid[c]&&p.channel_valid[c]&&std::abs(x.phase[c]-p.phase[c])>config_.max_phase_step)current.channel_valid[c]=false;
    }
    if(discontinuity||bad){ring_.clear();since_=0;++resets_;}
    session_=session;
    if(!bad){ring_.push_back(current);if(ring_.size()>needed_)ring_.pop_front();++since_;}
    out.buffered=ring_.size();out.resets=resets_;out.first_ns=ring_.empty()?x.time_ns:ring_.front().time_ns;
    out.result.status=bad?"invalid":"warming_up";
    if(bad)out.result.reasons.push_back("source_fault_or_motion");
    else if(discontinuity)out.result.reasons.push_back("new_continuity_epoch");
    if(ring_.size()==needed_&&since_>=stride_){
        PhaseWindow w;w.clock=clock_;w.clock_evidence=evidence_;w.samples.assign(ring_.begin(),ring_.end());
        out.result=analyze_phase(w,config_,backend_);since_=0;
    }else if(ring_.size()==needed_)out.result.status="waiting_next_analysis";
    return out;
}
}
