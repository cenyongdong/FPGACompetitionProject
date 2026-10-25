#include "reference.hpp"
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace pose::events {
    namespace {
        Vec3 sub(Vec3 a, Vec3 b) { return {a.x-b.x, a.y-b.y, a.z-b.z}; }
        Vec3 mid(Vec3 a, Vec3 b) { return {(a.x+b.x)/2, (a.y+b.y)/2, (a.z+b.z)/2}; }
        double dot(Vec3 a, Vec3 b) { return a.x*b.x+a.y*b.y+a.z*b.z; }
        double norm(Vec3 a) { return std::sqrt(dot(a,a)); }
        double angle(Vec3 a, Vec3 b) {
            const double d = norm(a)*norm(b);
            if (!(d > 1e-10)) throw std::domain_error("Degenerate joint geometry");
            return std::acos(std::clamp(dot(a,b)/d,-1.0,1.0))*180.0/3.14159265358979323846;
        }
        bool finite(Vec3 a) { return std::isfinite(a.x)&&std::isfinite(a.y)&&std::isfinite(a.z); }
        bool later(Ns a, Ns b, Ns interval) { return a >= b && a-b >= interval; }
    }
    Processor::Processor(Config config) : config_(std::move(config)) {
        const auto& c = config_;
        if (!(std::isfinite(c.score_min)&&c.score_min>=0&&c.score_min<=1&&
              std::isfinite(c.knee_stand_enter)&&std::isfinite(c.knee_stand_exit)&&
              std::isfinite(c.knee_sit_enter)&&std::isfinite(c.knee_sit_exit)&&
              c.knee_stand_enter<=180&&c.knee_stand_enter>c.knee_stand_exit&&
              c.knee_stand_exit>c.knee_sit_exit&&c.knee_sit_exit>c.knee_sit_enter&&c.knee_sit_enter>0&&
              std::isfinite(c.lean_enter)&&std::isfinite(c.lean_exit)&&c.lean_enter>c.lean_exit&&
              c.lean_exit>=0&&c.lean_enter<90&&std::isfinite(c.wrist_enter_ratio)&&
              std::isfinite(c.wrist_exit_ratio)&&c.wrist_enter_ratio>c.wrist_exit_ratio&&
              c.wrist_exit_ratio>=0&&c.confirm_ns&&c.hold_ns&&c.release_ns&&c.max_capture_gap_ns))
            throw std::invalid_argument("Invalid event thresholds/times");
        if(c.contract.mapping_evidence.size()>1024||c.contract.up_evidence.size()>1024)
            throw std::invalid_argument("Evidence references exceed bounded length");
        if (c.contract.mapping_verified) {
            if(c.contract.mapping_evidence.empty()) throw std::invalid_argument("Joint evidence required");
            const auto& j=c.contract.joints;
            std::array<int,12> ids={j.shoulder_l,j.shoulder_r,j.hip_l,j.hip_r,j.knee_l,j.knee_r,
                j.ankle_l,j.ankle_r,j.elbow_l,j.elbow_r,j.wrist_l,j.wrist_r};
            std::sort(ids.begin(),ids.end());
            if(ids.front()<0||ids.back()>=14||std::adjacent_find(ids.begin(),ids.end())!=ids.end())
                throw std::invalid_argument("Joint map must contain twelve distinct 0..13 indices");
        }
        if(c.contract.up_verified && (c.contract.up_evidence.empty()||!finite(c.contract.up)||
                                      std::abs(norm(c.contract.up)-1)>1e-6))
            throw std::invalid_argument("Verified unit up direction and evidence required");
    }
    void Processor::break_continuity() {
        have_previous_=false; stance_pending_=trunk_pending_=hold_active_=release_active_=false;
        latest_.features_valid=false;latest_.event_created=false;latest_.raised_mask=0;latest_.reasons|=Discontinuity;
        latest_.stance=Stance::Unknown; latest_.trunk=Trunk::Unknown; latest_.arms=Arms::Unknown;
        latest_.help=latest_.request_pending?Help::Latched:Help::Unknown;
    }
    Output Processor::observe(const Frame& f) {
        Output out;
        out.request_pending=latest_.request_pending; out.event_id=latest_.event_id;out.event_epoch=latest_.event_epoch;
        const auto& c=config_; const auto& contract=c.contract;
        if(!contract.mapping_verified) out.reasons|=MappingUnknown;
        if(!contract.up_verified) out.reasons|=UpUnknown;
        if(f.clock==Clock::Unknown||!f.capture_ns) out.reasons|=TimeUnknown;
        if(!f.subject_verified) out.reasons|=SubjectUnknown;
        if(!f.epoch||!f.sequence||!f.capture_sequence||f.segment.empty()||f.segment.size()>128) out.reasons|=IdentityUnknown;
        if(f.origin==Origin::Unknown) out.reasons|=OriginUnknown;
        // Synthetic timing may only establish synthetic behavior, never archive/live claims.
        if(f.clock==Clock::Synthetic&&f.origin!=Origin::Synthetic) out.reasons|=TimeUnknown;
        if(!std::isfinite(f.score)||!std::all_of(f.coordinates.begin(),f.coordinates.end(),
            [](float v){return std::isfinite(v);})) out.reasons|=InvalidPose;
        else if(f.score<c.score_min) out.reasons|=LowScore;
        const bool duplicate=have_previous_&&f.epoch==previous_.epoch&&f.sequence<=previous_.sequence;
        if(duplicate) out.reasons|=Duplicate;
        bool continuous=have_previous_&&f.epoch==previous_.epoch&&f.segment==previous_.segment&&
            f.clock==previous_.clock&&f.origin==previous_.origin&&f.sequence==previous_.sequence+1&&
            f.capture_sequence==previous_.capture_sequence+1&&f.capture_ns>previous_.capture_ns&&
            f.capture_ns-previous_.capture_ns<=c.max_capture_gap_ns&&f.now_ns>=previous_.now_ns;
        if(!continuous) {
            stance_pending_=trunk_pending_=hold_active_=release_active_=false;
            if(have_previous_&&!duplicate) out.reasons|=Discontinuity;
        }
        const auto fatal=out.reasons&~std::uint32_t(Discontinuity);
        if(fatal) {
            stance_pending_=trunk_pending_=hold_active_=release_active_=false;
            out.help=out.request_pending?Help::Latched:Help::Unknown;
            // Duplicate/old frames never replace the most recent accepted sequence.
            if(!duplicate&&f.segment.size()<=128) {previous_=f;have_previous_=true;}
            latest_=out; return out;
        }
        auto point=[&](int i){return Vec3{f.coordinates[3*i],f.coordinates[3*i+1],f.coordinates[3*i+2]};};
        const auto& j=contract.joints;
        try {
            const auto sl=point(j.shoulder_l),sr=point(j.shoulder_r),hl=point(j.hip_l),hr=point(j.hip_r);
            const auto kl=point(j.knee_l),kr=point(j.knee_r),al=point(j.ankle_l),ar=point(j.ankle_r);
            const auto torso=sub(mid(sl,sr),mid(hl,hr)); const double scale=norm(torso);
            if(!(scale>1e-5)) throw std::domain_error("Zero torso");
            out.knee_degrees=(angle(sub(hl,kl),sub(al,kl))+angle(sub(hr,kr),sub(ar,kr)))/2;
            out.trunk_degrees=angle(torso,contract.up);
            auto raised=[&](Vec3 shoulder,Vec3 elbow,Vec3 wrist,unsigned side){
                const double h=dot(sub(wrist,shoulder),contract.up)/scale;
                const double e=dot(sub(elbow,shoulder),contract.up)/scale;
                const double threshold=(continuous&&(latest_.raised_mask&side))?c.wrist_exit_ratio:c.wrist_enter_ratio;
                return std::pair<double,bool>{h,h>=threshold&&e>=0};
            };
            const auto left=raised(sl,point(j.elbow_l),point(j.wrist_l),1);
            const auto right=raised(sr,point(j.elbow_r),point(j.wrist_r),2);
            out.raised_mask=(left.second?1u:0u)|(right.second?2u:0u);
            out.wrist_ratio=std::max(left.first,right.first);
            out.arms=(left.second||right.second)?Arms::Raised:Arms::Down;
            out.features_valid=true;
        } catch(const std::domain_error&) {
            out.reasons|=Degenerate; out.help=out.request_pending?Help::Latched:Help::Unknown;
            stance_pending_=trunk_pending_=hold_active_=release_active_=false;
            previous_=f;have_previous_=true;latest_=out;return out;
        }
        const auto prior_stance=continuous?latest_.stance:Stance::Unknown;
        Stance proposed=Stance::Unknown;
        if(out.knee_degrees>=c.knee_stand_enter||(prior_stance==Stance::Standing&&out.knee_degrees>=c.knee_stand_exit))
            proposed=Stance::Standing;
        else if(out.knee_degrees<=c.knee_sit_enter||(prior_stance==Stance::Sitting&&out.knee_degrees<=c.knee_sit_exit))
            proposed=Stance::Sitting;
        if(!stance_pending_||proposed!=pending_stance_) {
            pending_stance_=proposed;stance_begin_=f.capture_ns;stance_pending_=true;
        }
        if(proposed!=Stance::Unknown&&later(f.capture_ns,stance_begin_,c.confirm_ns)) out.stance=proposed;
        else if(proposed==prior_stance) out.stance=prior_stance;
        Trunk trunk=(out.trunk_degrees>=c.lean_enter||
            (continuous&&latest_.trunk==Trunk::Leaning&&out.trunk_degrees>=c.lean_exit))?Trunk::Leaning:Trunk::Upright;
        if(!trunk_pending_||trunk!=pending_trunk_) {pending_trunk_=trunk;trunk_begin_=f.capture_ns;trunk_pending_=true;}
        if(later(f.capture_ns,trunk_begin_,c.confirm_ns)) out.trunk=trunk;
        else if(continuous&&trunk==latest_.trunk) out.trunk=latest_.trunk;
        if(out.request_pending) out.help=Help::Latched;
        else if(!released_) {
            out.help=Help::AwaitRelease;
            if(out.arms==Arms::Down) {
                if(!release_active_) {release_active_=true;release_begin_=f.capture_ns;}
                if(later(f.capture_ns,release_begin_,c.release_ns)) {released_=true;out.help=Help::Ready;}
            } else release_active_=false;
        } else if(out.arms==Arms::Raised) {
            if(!hold_active_||!(holding_arms_&out.raised_mask)) {
                hold_active_=true;hold_begin_=f.capture_ns;holding_arms_=out.raised_mask;
            } else holding_arms_&=out.raised_mask;
            out.help=Help::Holding;
            if(later(f.capture_ns,hold_begin_,c.hold_ns)) {
                out.event_id=next_event_++;out.event_epoch=f.epoch;out.event_created=true;out.request_pending=true;
                out.help=Help::Latched;released_=false;hold_active_=false;
            }
        } else {hold_active_=false;out.help=Help::Ready;}
        previous_=f;have_previous_=true;latest_=out;return out;
    }
    bool Processor::acknowledge(std::uint64_t epoch,std::uint64_t id) {
        if(!latest_.request_pending||epoch!=latest_.event_epoch||id!=latest_.event_id) return false;
        latest_.request_pending=false;latest_.help=Help::AwaitRelease;
        latest_.event_created=false;
        hold_active_=release_active_=false;released_=false;return true;
    }
    PlSimulator::PlSimulator(Ns a,Ns b):service_timeout_(a),result_timeout_(b) {
        if(!a||!b) throw std::invalid_argument("Zero feedback timeout");
    }
    void PlSimulator::time(Ns now) {if(now<now_) throw std::invalid_argument("Feedback time regressed");now_=now;}
    void PlSimulator::begin(Ns now,std::uint64_t epoch) {
        time(now);if(!epoch) throw std::invalid_argument("Zero epoch");
        if(started_&&epoch==epoch_) throw std::invalid_argument("Restart requires a new epoch");
        epoch_=epoch;began_=now;started_=true;have_heartbeat_=have_input_=have_result_=false;
        stopped_=fault_=false;heartbeat_sequence_=input_sequence_=result_sequence_=0;
        feedback_.availability=Availability::Initializing;
    }
    bool PlSimulator::heartbeat(Ns now,std::uint64_t epoch,std::uint64_t seq) {
        time(now);if(!started_||stopped_||fault_||epoch!=epoch_||seq<=heartbeat_sequence_) return false;
        heartbeat_sequence_=seq;last_heartbeat_=now;have_heartbeat_=true;return true;
    }
    bool PlSimulator::input(Ns now,std::uint64_t epoch,std::uint64_t seq) {
        time(now);if(!started_||stopped_||fault_||epoch!=epoch_||seq<=input_sequence_) return false;
        input_sequence_=seq;last_input_=now;have_input_=true;return true;
    }
    bool PlSimulator::result(const Frame& f,const Output& out) {
        time(f.now_ns);
        if(!started_||stopped_||fault_||f.epoch!=epoch_||f.sequence<=result_sequence_) return false;
        result_sequence_=f.sequence;last_result_=f.now_ns;have_result_=true;
        if(out.request_pending&&out.event_id&&!feedback_.request_pending&&out.event_epoch==f.epoch&&
           (out.event_epoch!=feedback_.event_epoch||out.event_id>feedback_.event_id)) {
            feedback_.event_id=out.event_id;feedback_.event_epoch=out.event_epoch;feedback_.request_pending=true;
        }
        if(f.origin==Origin::ArchivedInference||f.origin==Origin::Unknown||
           (out.reasons&(MappingUnknown|UpUnknown|TimeUnknown|SubjectUnknown|OriginUnknown)))
            reported_=Availability::Unverified;
        else if(!out.features_valid) reported_=Availability::NoReliablePose;
        else reported_=f.origin==Origin::Synthetic?Availability::Synthetic:Availability::Available;
        return true;
    }
    bool PlSimulator::acknowledge(Ns now,std::uint64_t epoch,std::uint64_t id) {
        time(now);if(!feedback_.request_pending||epoch!=feedback_.event_epoch||id!=feedback_.event_id) return false;
        feedback_.request_pending=false;return true;
    }
    void PlSimulator::stop(Ns now,bool fault) {time(now);stopped_=!fault;fault_=fault;}
    Feedback PlSimulator::tick(Ns now) {
        time(now);
        feedback_.service_alive=have_heartbeat_&&!later(now,last_heartbeat_,service_timeout_);
        feedback_.input_recent=have_input_&&!later(now,last_input_,result_timeout_);
        feedback_.result_recent=have_result_&&!later(now,last_result_,result_timeout_);
        if(fault_) feedback_.availability=Availability::Fault;
        else if(stopped_) feedback_.availability=Availability::Stopped;
        else if(!started_) feedback_.availability=Availability::Initializing;
        else if(!feedback_.service_alive&&later(now,have_heartbeat_?last_heartbeat_:began_,service_timeout_))
            feedback_.availability=Availability::ServiceLost;
        else if(!have_heartbeat_) feedback_.availability=Availability::Initializing;
        else if(have_input_&&!feedback_.input_recent) feedback_.availability=Availability::InputStale;
        else if(have_result_&&!feedback_.result_recent) feedback_.availability=Availability::ResultStale;
        else if(!have_result_) feedback_.availability=Availability::Initializing;
        else if(!have_input_) feedback_.availability=Availability::Unverified;
        else feedback_.availability=reported_;
        return feedback_;
    }
    const char* name(Stance s) {switch(s){case Stance::Standing:return "standing";case Stance::Sitting:return "sitting";default:return "unknown";}}
    const char* name(Trunk s) {switch(s){case Trunk::Upright:return "upright";case Trunk::Leaning:return "leaning";default:return "unknown";}}
    const char* name(Arms s) {switch(s){case Arms::Down:return "down";case Arms::Raised:return "raised";default:return "unknown";}}
    const char* name(Help s) {switch(s){case Help::Ready:return "ready";case Help::Holding:return "holding";case Help::Latched:return "latched";case Help::AwaitRelease:return "await_release";default:return "unknown";}}
    const char* name(Availability s) {switch(s){case Availability::Unverified:return "unverified";case Availability::Synthetic:return "synthetic_only";case Availability::Available:return "available";case Availability::NoReliablePose:return "no_reliable_pose";case Availability::InputStale:return "input_stale";case Availability::ResultStale:return "result_stale";case Availability::ServiceLost:return "service_lost";case Availability::Stopped:return "stopped";case Availability::Fault:return "fault";default:return "initializing";}}
}
