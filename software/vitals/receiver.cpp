#include "receiver.hpp"
#include "fir_coefficients.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace pose::vitals {
namespace {
constexpr double pi=3.14159265358979323846;
std::uint64_t grid_ns(std::uint64_t tick){return tick/600*1000000000ULL+tick%600*1000000000ULL/600;}
}
void ReceiverResampler::invalidate(){have_=false;filled_=write_=0;next_dense_=0;sequence_=0;
    if(epoch_==std::numeric_limits<std::uint64_t>::max())throw std::runtime_error("Vitals epoch exhausted");
    ++epoch_;
}
void ReceiverResampler::initialize(const ReceiverSample& x,const std::array<double,channels>& phase){
    have_=true;previous_=x;wrapped_=unwrapped_=phase;base_ns_=x.time_ns;next_dense_=1;write_=1;filled_=1;dense_[0]=phase;sequence_=0;broken_={};last_bad_ns_={};
}
void ReceiverResampler::append(const std::array<double,channels>& value,std::uint64_t tick,Resampled& result){
    dense_[write_]=value;write_=(write_+1)%481;filled_=std::min<std::size_t>(481,filled_+1);
    if(filled_!=481||tick<480||(tick-240)%12!=0)return;
    PhaseSample sample;sample.time_ns=base_ns_+grid_ns(tick-240);sample.sequence=++sequence_;sample.source_support_valid=true;
    for(std::size_t ch=0;ch<channels;++ch)sample.channel_valid[ch]=!broken_[ch]||base_ns_+grid_ns(tick-480)>=last_bad_ns_[ch];
    for(std::size_t t=0;t<481;++t)for(std::size_t ch=0;ch<channels;++ch)
        sample.phase[ch]+=fir_coefficients[t]*dense_[(write_+t)%481][ch];
    result.samples.push_back(sample);
}
Resampled ReceiverResampler::push(const ReceiverSample& x){
    if(!x.session)throw std::invalid_argument("Receiver session must be nonzero");
    Resampled out;std::array<double,channels> phase{};bool valid=x.valid;
    for(std::size_t ch=0;ch<channels;++ch){const auto&p=x.pairs[ch];
        auto a=std::max(std::abs(p.first.real()),std::abs(p.first.imag()));auto b=std::max(std::abs(p.second.real()),std::abs(p.second.imag()));
        if(!std::isfinite(p.first.real())||!std::isfinite(p.first.imag())||!std::isfinite(p.second.real())||!std::isfinite(p.second.imag())||a<1e-12||b<1e-12){valid=false;continue;}
        phase[ch]=std::arg((p.first/a)*std::conj(p.second/b));
    }
    if(!valid){invalidate();out.reset=true;out.reason="invalid_raw_antenna_pair";out.epoch=epoch_;return out;}
    if(!have_){initialize(x,phase);out.epoch=epoch_;return out;}
    std::string fault;
    if(x.session!=previous_.session)fault="receiver_session_changed";
    else if(x.time_ns<=previous_.time_ns||x.event_sequence<=previous_.event_sequence)fault="receiver_clock_or_identity_reset";
    else if(x.time_ns-previous_.time_ns>10000000)fault="receiver_gap";
    std::array<double,channels> next=unwrapped_;
    if(fault.empty())for(std::size_t ch=0;ch<channels;++ch){const auto delta=std::remainder(phase[ch]-wrapped_[ch],2*pi);
        if(std::abs(delta)>.25){broken_[ch]=true;last_bad_ns_[ch]=x.time_ns;next[ch]=phase[ch];}
        else next[ch]+=delta;
    }
    if(!fault.empty()){invalidate();initialize(x,phase);out.reset=true;out.reason=fault;out.epoch=epoch_;return out;}
    const auto span=x.time_ns-previous_.time_ns;
    while(grid_ns(next_dense_)<=x.time_ns-base_ns_){
        const auto stamp=base_ns_+grid_ns(next_dense_);
        const double fraction=double(stamp-previous_.time_ns)/span;
        std::array<double,channels> value{};
        for(std::size_t ch=0;ch<channels;++ch)value[ch]=unwrapped_[ch]+fraction*(next[ch]-unwrapped_[ch]);
        append(value,next_dense_,out);++next_dense_;
    }
    previous_=x;wrapped_=phase;unwrapped_=next;out.epoch=epoch_;return out;
}
std::vector<StreamUpdate> ReceiverStream::push(const ReceiverSample& x){
    const auto resampled=resampler_.push(x);std::vector<StreamUpdate> out;
    if(resampled.reset){PhaseSample invalid;invalid.time_ns=x.time_ns;auto item=stream_.push(resampled.epoch,invalid);item.result.reasons={resampled.reason};out.push_back(std::move(item));}
    for(const auto& sample:resampled.samples)out.push_back(stream_.push(resampled.epoch,sample));
    return out;
}
}
