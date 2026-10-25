#include "ingress.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <deque>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace nexmon_board {
namespace {
constexpr std::int64_t hz=300, scale=1000000, half=500000, tolerance=250000;
std::uint16_t u16(const std::uint8_t* p) { return p[0]|std::uint16_t(p[1])<<8; }
std::uint32_t u32(const std::uint8_t* p) { return u16(p)|std::uint32_t(u16(p+2))<<16; }
std::int64_t floor_div(std::int64_t a,std::int64_t b) { auto q=a/b,r=a%b; return q-(r<0); }
std::int64_t modulo(std::int64_t a,std::int64_t b) { return a-floor_div(a,b)*b; }
double modulo(double a,double b) { auto v=std::fmod(a,b); return v<0?v+b:v; }
void require(bool ok,const char* why) { if(!ok) throw std::runtime_error(why); }

struct Meta {
    std::uint16_t seq=0,config=0,channel=0,fc=0,qos=0,tsf=0,counter=0,frame_size=0;
    std::uint32_t hook=0;
    std::array<std::uint32_t,3> original{};
    std::int64_t arrival=0;
};
bool same_event(const Meta&a,const Meta&b) {
    return std::tie(a.seq,a.channel,a.fc,a.qos,a.tsf,a.counter)==
           std::tie(b.seq,b.channel,b.fc,b.qos,b.tsf,b.counter);
}
struct Part { Meta meta; std::array<std::uint32_t,64> words{}; };
struct Event {
    Meta meta;
    std::array<std::array<std::uint32_t,64>,3> words{};
    std::array<std::array<std::uint32_t,3>,3> original{};
    std::int64_t time=0;
    bool keep=false;
};
struct Cell { std::int64_t target=0; std::int64_t index=-1; };
using Key=std::pair<std::uint16_t,std::uint16_t>; // full Sequence Control + FC sans retry
Key identity(const Event&e) { return {e.meta.seq,std::uint16_t(e.meta.fc&~0x800)}; }

struct History : std::deque<Event> {
    std::size_t base=0;
    Event& operator[](std::size_t i){return at(i-base);}
    const Event& operator[](std::size_t i)const{return at(i-base);}
    std::size_t next()const{return base+size();}
};

struct Node {
    const Config* config=nullptr;
    NodeSummary summary;
    bool pending=false,previous=false,have_arrival=false,failed=false;
    Part csi;
    std::vector<Part> group;
    Meta previous_meta;
    std::int64_t last_arrival=0,first_arrival=0,local_us=0;
    std::size_t sequence_span=0;
    History events;
    std::map<Key,std::size_t> kept;
    std::map<std::uint16_t,std::pair<std::int64_t,std::size_t>> recent;
    std::vector<std::int64_t> prefix;
    std::int64_t grid_previous=-1,slot=0,first_slot=0,best=-1;
    std::vector<Cell> block;
    std::map<std::int64_t,Cell> cells;

    void prune() {
        if(!config->streaming)return;
        const auto cutoff=local_us-4000000;
        while(events.size()>1 && events.front().time<cutoff) {
            auto it=kept.find(identity(events.front()));
            if(it!=kept.end()&&it->second==events.base)kept.erase(it);
            events.pop_front();++events.base;
        }
        for(auto it=cells.begin();it!=cells.end();) {
            if(it->second.target<cutoff*hz || (it->second.index>=0&&std::size_t(it->second.index)<events.base))it=cells.erase(it);
            else ++it;
        }
        require(events.size()<=2048&&cells.size()<=1600,"Rolling CSI history budget exceeded; resync required");
    }

    void reset_clock() {
        ++summary.clock_resets; failed=true;
        previous=false;local_us=0;recent.clear();prefix.clear();block.clear();best=-1;
    }
    void expire(std::int64_t now) {
        if(have_arrival && now-last_arrival>=32768) {
            reset_clock();have_arrival=false;pending=false;group.clear();
        } else if(pending && now-csi.meta.arrival>20000) {
            ++summary.pairing_errors;pending=false;group.clear();reset_clock();
        }
    }
    void phase_lock(std::int64_t now) {
        double re=0,im=0;
        const double tau=2*std::acos(-1.0);
        for(auto t:prefix) { auto residue=modulo((t-prefix.front())*hz,scale);
            auto angle=tau*double(residue)/double(scale);re+=std::cos(angle);im+=std::sin(angle); }
        re/=double(prefix.size());im/=double(prefix.size());
        const auto seed=std::atan2(im,re)*double(scale)/tau;
        std::vector<double> offsets;
        for(auto t:prefix) offsets.push_back(modulo(double(modulo((t-prefix.front())*hz,scale))-seed+half,double(scale))-half);
        std::sort(offsets.begin(),offsets.end());
        auto median=offsets[offsets.size()/2];
        if(offsets.size()%2==0) median=(median+offsets[offsets.size()/2-1])/2;
        const auto relative=modulo(std::int64_t(std::nearbyint(seed+median)),scale);
        summary.phase_scaled=modulo(prefix.front()*hz+relative,scale);
        summary.concentration=std::hypot(re,im);
        summary.locked=prefix.size()>=120 && summary.concentration>=.75;
        summary.calibration_end_us=now;prefix.clear();
        if(!summary.locked) { failed=true;return; }
        slot=floor_div(now*hz+half-summary.phase_scaled,scale)+1;first_slot=slot;
    }
    void feed_grid(std::size_t index) {
        auto now=events[index].time;
        if(grid_previous>=0) require(now>grid_previous && now-grid_previous<32768,"Retained event clock discontinuity");
        grid_previous=now;
        if(failed)return;
        if(!summary.locked) {
            if(prefix.size()>=1024) { failed=true;prefix.clear();return; }
            prefix.push_back(now);
            if(now-prefix.front()>=1000000)phase_lock(now);
            return;
        }
        auto centre=summary.phase_scaled+slot*scale;
        while(now*hz>=centre+half) {
            block.push_back({centre,best});best=-1;++slot;
            if(block.size()==20) {
                for(std::size_t i=0;i<20;++i)cells.emplace(slot-20+std::int64_t(i),block[i]);
                block.clear();
            }
            centre=summary.phase_scaled+slot*scale;
        }
        if(now*hz>=centre-half && (best<0 ||
            std::make_tuple(std::abs(now*hz-centre),now,index)<
            std::make_tuple(std::abs(events[std::size_t(best)].time*hz-centre),events[std::size_t(best)].time,std::size_t(best))))best=std::int64_t(index);
    }
    void complete() {
        require(events.size()<(config->streaming?2048:config->expected_events*2),"Complete-event budget exceeded");
        Event event;event.meta=group.front().meta;bool valid=true;
        for(const auto& p:group) {
            auto core=p.meta.config>>8;event.words[core]=p.words;event.original[core]=p.meta.original;
            require(p.meta.frame_size==event.meta.frame_size,"Raw frame size differs across cores");
            bool nonzero=false;
            for(std::size_t i=0;i<64;++i)if(i<28 || i>30) {
                auto z=decode_acphy(p.words[i]);require(std::isfinite(z.real())&&std::isfinite(z.imag()),"Non-finite native CSI");
                nonzero|=z!=std::complex<double>{};
            }
            valid &= nonzero;
        }
        group.clear();++summary.complete_events;
        if(previous) {
            auto host=event.meta.arrival-previous_meta.arrival;
            auto delta=std::uint16_t(event.meta.tsf-previous_meta.tsf);
            auto step=std::uint16_t(event.meta.counter-previous_meta.counter);
            if(!(host>0&&host<32768&&delta>0&&delta<32768&&step==1))reset_clock();
            else local_us+=delta;
        }
        event.time=local_us;previous_meta=event.meta;previous=true;
        for(auto it=recent.begin();it!=recent.end();) {
            if(event.meta.arrival-it->second.first>20000)it=recent.erase(it);else ++it;
        }
        const auto index=events.next();
        if(!valid)++summary.invalid_events;
        else {
            auto old=recent.find(event.meta.seq);
            if(old!=recent.end()) {
                if(event.meta.fc&0x800)++summary.retransmissions;
                else failed=true;
            } else event.keep=true;
            recent[event.meta.seq]={event.meta.arrival,index};
            require(recent.size()<=1024,"Dedup memory budget exceeded");
        }
        if(event.keep) {
            require((event.meta.fc&~0x800)==0x8 && !(event.meta.seq&15),"Unexpected bounded broadcast sequence profile");
            require(kept.size()<(config->streaming?2048:config->expected_events),"Retained event budget exceeded");
            require(!kept.count(identity(event)),"Sequence identity reused across bounded job");
            if(!kept.empty()) {
                // Last retained event by arrival, not numeric map order (wrap).
                auto prev=std::find_if(events.rbegin(),events.rend(),[](const Event&e){return e.keep;});
                require(prev!=events.rend(),"Missing prior retained event");
                auto a=prev->meta.seq>>4,b=event.meta.seq>>4,d=(b-a)&4095;
                require(d>0&&d<2048,"Ambiguous sequence step or mixed job");
                sequence_span+=std::size_t(d);
                require(config->streaming||sequence_span<config->expected_events,"Sequence span exceeds declared bounded TX job");
                if(b<a)++summary.wraps;
                require(prev->meta.frame_size==event.meta.frame_size,"Fixed TX profile changed frame length");
            }
            kept.emplace(identity(event),index);++summary.retained;
        }
        events.push_back(std::move(event));
        if(events.back().keep)feed_grid(index);
        prune();
    }
    void feed(std::int64_t arrival,std::uint16_t port,const std::uint8_t*p,std::size_t n) {
        if(port!=5500&&port!=5501)return;
        require(!have_arrival||arrival>=last_arrival,"Arrival clock moved backwards");
        expire(arrival);if(!have_arrival)first_arrival=arrival;
        require(config->streaming||arrival-first_arrival<=12000000,"Bounded acquisition exceeded twelve seconds");
        last_arrival=arrival;have_arrival=true;
        ++summary.packets;require(config->streaming||summary.packets<=config->expected_events*12,"Packet budget exceeded");
        require(p!=nullptr,"Null datagram");
        if(port==5500) {
            require(n==274&&u16(p)==0x1111&&u16(p+16)==106,"CSI format/bandwidth/chip mismatch");
            require(std::equal(config->transmitter_mac.begin(),config->transmitter_mac.end(),p+4)&&u16(p+14)==config->chanspec,"CSI transmitter/channel changed");
            auto core=u16(p+12);require(core==0||core==256||core==512,"CSI core/stream mismatch");
            if(pending) { ++summary.pairing_errors;group.clear();reset_clock(); }
            csi={};csi.meta.seq=u16(p+10);csi.meta.config=core;csi.meta.channel=u16(p+14);csi.meta.arrival=arrival;
            for(std::size_t i=0;i<64;++i)csi.words[i]=u32(p+18+4*i);
            pending=true;return;
        }
        require(n==50&&std::memcmp(p,"NMD3",4)==0&&u16(p+4)==3&&u16(p+6)==50,"Require unchanged NMD3/50 diagnostics");
        require(std::equal(config->transmitter_mac.begin(),config->transmitter_mac.end(),p+8)&&u16(p+18)==config->chanspec,"Metadata transmitter/channel changed");
        Meta m;m.seq=u16(p+14);m.config=u16(p+16);m.channel=u16(p+18);m.fc=u16(p+20);m.qos=u16(p+22);m.tsf=u16(p+24);m.counter=u16(p+26);
        require(m.config==0||m.config==256||m.config==512,"Metadata core/stream mismatch");
        require(u16(p+28)==28&&u16(p+30)==3,"Pre-overwrite word sidecar mismatch");
        for(std::size_t i=0;i<3;++i)m.original[i]=u32(p+32+4*i);
        m.frame_size=u16(p+44);m.hook=u32(p+46);
        if(!pending||m.seq!=csi.meta.seq||m.config!=csi.meta.config||m.channel!=csi.meta.channel) {
            pending=false;++summary.pairing_errors;group.clear();reset_clock();return;
        }
        pending=false;m.arrival=csi.meta.arrival;csi.meta=m;
        if(!group.empty()&&!same_event(group.front().meta,m)) { ++summary.incomplete_groups;group.clear();reset_clock(); }
        for(const auto& part:group)if(part.meta.config==m.config) { ++summary.incomplete_groups;group.clear();reset_clock();return; }
        group.push_back(csi);if(group.size()==3)complete();
    }
};
}

std::complex<double> decode_acphy(std::uint32_t w) {
    int exponent=int(w&63);if(exponent&32)exponent-=64;
    int re=int((w>>18)&2047),im=int((w>>6)&2047);
    if(w&(1u<<29))re=-re;
    if(w&(1u<<17))im=-im;
    return {std::ldexp(double(re),exponent),std::ldexp(double(im),exponent)};
}

struct Ingress::Impl {
    Config config;std::array<Node,3> nodes;
    BatchResult result;bool finished=false,anchored=false,started=false,poisoned=false;
    std::int64_t next_slot=0;std::size_t ready_index=0;
    explicit Impl(Config c):config(std::move(c)) {
        require(!config.session_id.empty()&&config.session_id.size()<=128,"Explicit bounded session required");
        require(std::set<std::string>(config.receiver_ids.begin(),config.receiver_ids.end()).size()==3,"Require distinct receiver identities");
        for(const auto&s:config.receiver_ids)require(!s.empty()&&s.size()<=128,"Receiver identity missing/too long");
        require(config.expected_events>0&&config.expected_events<=3000,"Require one bounded <=3000-event TX job");
        require((config.chanspec&0x3800)==0x1000,"Require explicit HT/VHT20 chanspec");
        for(double g:config.gains)require(std::isfinite(g)&&g>0,"Require explicit finite positive candidate gains");
        require(std::any_of(config.transmitter_mac.begin(),config.transmitter_mac.end(),[](auto v){return v!=0;}),"Missing transmitter MAC");
        for(auto&n:nodes)n.config=&config;
        result.session_id=config.session_id;
    }
    std::int64_t local_slot(const Event&e,const Node&n)const {return floor_div(e.time*hz-n.summary.phase_scaled+half,scale);}
    void update() {
        require(!poisoned,"Ingress session rejected; create a new acquisition session");
        for(const auto&n:nodes)require(!n.failed&&!n.summary.clock_resets,"Unproven clock/pairing/sequence segment; end this session");
        std::uint16_t frame_size=0;bool have_size=false;
        for(const auto&n:nodes)if(!n.kept.empty()) {
            const auto size=n.events[n.kept.begin()->second].meta.frame_size;
            require(!have_size||size==frame_size,"Receivers disagree on bounded TX frame profile");
            frame_size=size;have_size=true;
        }
        if(!anchored) {
            if(!std::all_of(nodes.begin(),nodes.end(),[](const Node&n){return n.summary.locked;}))return;
            for(const auto&e:nodes[0].events)if(e.keep) {
                auto key=identity(e);bool common=true;std::array<const Event*,3> trip{};
                for(std::size_t r=0;r<3;++r) {
                    auto it=nodes[r].kept.find(key);
                    if(it==nodes[r].kept.end()) {common=false;break;}
                    trip[r]=&nodes[r].events[it->second];
                    if(trip[r]->time<=nodes[r].summary.calibration_end_us) {common=false;break;}
                }
                if(!common)continue;
                const auto origin=local_slot(*trip[0],nodes[0]);
                for(std::size_t r=0;r<3;++r)result.slot_shifts[r]=origin-local_slot(*trip[r],nodes[r]);
                anchored=true;break;
            }
            if(!anchored)return;
        }
        if(!std::all_of(nodes.begin(),nodes.end(),[](const Node&n){return !n.cells.empty();}))return;
        if(!started) {
            auto first=nodes[0].cells.begin()->first;
            for(std::size_t r=1;r<3;++r)first=std::max(first,nodes[r].cells.begin()->first+result.slot_shifts[r]);
            first+=modulo(nodes[0].cells.begin()->first-first,std::int64_t(20));
            next_slot=first;started=true;
        }
        auto last=nodes[0].cells.rbegin()->first;
        for(std::size_t r=1;r<3;++r)last=std::min(last,nodes[r].cells.rbegin()->first+result.slot_shifts[r]);
        while(next_slot+19<=last) {
            WindowDecision d;d.start_reference_slot=next_slot;
            std::array<std::array<const Event*,20>,3> selected{};
            for(std::size_t t=0;t<20;++t) {
                bool present=true;
                for(std::size_t r=0;r<3;++r) {
                    auto it=nodes[r].cells.find(next_slot+std::int64_t(t)-result.slot_shifts[r]);
                    if(it==nodes[r].cells.end()||it->second.index<0) {d.missing_cell=true;present=false;continue;}
                    const auto&e=nodes[r].events[std::size_t(it->second.index)];selected[r][t]=&e;
                    if(std::abs(e.time*hz-it->second.target)>tolerance)d.point_error=true;
                }
                if(present && !(identity(*selected[0][t])==identity(*selected[1][t])&&identity(*selected[1][t])==identity(*selected[2][t])))d.different_event=true;
                if(present)require(selected[0][t]->meta.frame_size==selected[1][t]->meta.frame_size&&selected[1][t]->meta.frame_size==selected[2][t]->meta.frame_size,"Common identity has conflicting raw frame length");
            }
            d.valid=!(d.missing_cell||d.point_error||d.different_event);
            if(!config.streaming)result.decisions.push_back(d);
            if(d.valid) {
                JointWindow w;w.start_reference_slot=next_slot;
                w.source_time_ns=std::uint64_t(selected[0][19]->meta.arrival)*1000;
                for(std::size_t r=0;r<3;++r)for(std::size_t t=0;t<20;++t) {
                    const auto&e=*selected[r][t];w.event_indices[r][t]=std::uint32_t(nodes[r].cells.at(next_slot+std::int64_t(t)-result.slot_shifts[r]).index);
                    for(std::size_t a=0;a<3;++a)for(std::size_t n=0;n<30;++n) {
                        auto bin=std::size_t((ht20_ng2[n]+64)%64);
                        auto word=(bin>=28&&bin<=30)?e.original[a][bin-28]:e.words[a][bin];
                        auto value=decode_acphy(word)*config.gains[r];
                        require(std::isfinite(value.real())&&std::isfinite(value.imag()),"Gain produced non-finite CSI");
                        w.csi[((r*3+a)*20+t)*30+n]=value;
                    }
                }
                require(!config.streaming||result.windows.size()<32,"Ready window budget exceeded; consume or resync");
                result.windows.push_back(std::move(w));
            }
            next_slot+=20;
            if(config.streaming)for(std::size_t r=0;r<3;++r) {
                auto& cells=nodes[r].cells;
                cells.erase(cells.begin(),cells.lower_bound(next_slot-result.slot_shifts[r]));
            }
        }
    }
};

Ingress::Ingress(Config config):impl_(std::make_unique<Impl>(std::move(config))){}
Ingress::~Ingress()=default;
Ingress::Ingress(Ingress&&)noexcept=default;
Ingress&Ingress::operator=(Ingress&&)noexcept=default;
void Ingress::feed(std::size_t receiver,std::string_view session,std::int64_t arrival,std::uint16_t port,const std::uint8_t*p,std::size_t n) {
    require(bool(impl_)&&!impl_->finished,"Ingress session already finalized");
    try {
        require(!impl_->poisoned,"Ingress session rejected; create a new acquisition session");
        require(receiver<3,"Receiver index out of range");
        require(session==impl_->config.session_id,"Different or missing acquisition session");
        impl_->nodes[receiver].feed(arrival,port,p,n);impl_->update();
    }catch(...){impl_->poisoned=true;throw;}
}
void Ingress::expire(std::size_t receiver,std::int64_t arrival) {
    require(bool(impl_)&&!impl_->finished&&receiver<3,"Invalid expire target/session");
    try {impl_->nodes[receiver].expire(arrival);impl_->update();}
    catch(...){impl_->poisoned=true;throw;}
}
std::vector<JointWindow> Ingress::take_ready() {
    require(bool(impl_)&&!impl_->finished&&!impl_->poisoned,"Ingress session already finalized or rejected");
    std::vector<JointWindow> out;
    if(impl_->config.streaming){out.swap(impl_->result.windows);return out;}
    const auto&all=impl_->result.windows;
    for(;impl_->ready_index<all.size();++impl_->ready_index)out.push_back(all[impl_->ready_index]);
    return out;
}
BatchResult Ingress::finish() {
    require(bool(impl_)&&!impl_->finished,"Ingress session already finalized");
    impl_->update();require(impl_->anchored&&impl_->started,"No common post-startup finalized grid");
    for(std::size_t r=0;r<3;++r) {
        auto&n=impl_->nodes[r];n.summary.trailing_unpaired=n.pending;n.summary.trailing_cores=n.group.size();impl_->result.nodes[r]=n.summary;
    }
    for(const auto&kv:impl_->nodes[0].kept)if(impl_->nodes[1].kept.count(kv.first)&&impl_->nodes[2].kept.count(kv.first))++impl_->result.common_events;
    impl_->finished=true;return std::move(impl_->result);
}
std::array<std::size_t,3> Ingress::retained_events()const {
    return {impl_->nodes[0].events.size(),impl_->nodes[1].events.size(),impl_->nodes[2].events.size()};
}
std::array<std::size_t,3> Ingress::retained_cells()const {
    return {impl_->nodes[0].cells.size(),impl_->nodes[1].cells.size(),impl_->nodes[2].cells.size()};
}
std::vector<std::uint8_t> encode_piwcsi2(const JointWindow&w,std::uint64_t frame,std::uint64_t source) {
    static_assert(sizeof(double)==8&&std::numeric_limits<double>::is_iec559,"IEEE754 float64 required");
    std::vector<std::uint8_t> out(piwcsi2_bytes);
    std::memcpy(out.data(),"PIWCSI2\0",8);
    auto put=[&](std::size_t at,std::uint64_t value,std::size_t n) {for(std::size_t i=0;i<n;++i)out[at+i]=std::uint8_t(value>>(8*i));};
    put(8,2,4);put(12,86400,4);put(16,frame,8);put(24,source,8);
    for(std::size_t i=0;i<csi_values;++i) {
        auto re=w.csi[i].real(),im=w.csi[i].imag();require(std::isfinite(re)&&std::isfinite(im),"Cannot serialize non-finite CSI");
        std::uint64_t a,b;std::memcpy(&a,&re,8);std::memcpy(&b,&im,8);put(32+i*16,a,8);put(40+i*16,b,8);
    }
    return out;
}
} // namespace nexmon_board
