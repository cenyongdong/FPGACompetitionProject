#include "system_timing.hpp"
#include "presaved_result_evidence.hpp"
#include <cstring>
#include <cmath>
#include <iomanip>
#include <stdexcept>

namespace pose::measurement {
namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
const pose::validation::FixtureWindow& fixtureFor(const std::vector<pose::validation::FixtureWindow>& cases,uint64_t id){
    need(cases.size()==27,"Timing fixture coverage differs");
    need(id>=transportBase&&id-transportBase<sentLimit,"Timing transport id outside finite range");
    return cases[(id-transportBase)%cases.size()];
}
void verify(const pose::validation::FixtureWindow& c,const pose_v1::application::Result& r,const pose_v1::Window& actual,size_t i){
    need(actual.source_time_ns==c.window.source_time_ns&&std::memcmp(actual.csi.data(),c.window.csi.data(),sizeof(actual.csi))==0,"Timing payload/reference identity differs");
    need(r.frame_id==actual.frame_id&&r.source_time_ns==actual.source_time_ns&&r.invocation==i&&!r.frozen_reference_checked,"Timing result invocation differs");
    need(r.before_forward==0&&r.completed_layers==745&&r.host_callbacks==7&&r.zg_callbacks==7,"Timing completion protocol differs");
    for(float v:r.input)need(std::isfinite(v),"Timing input nonfinite");
    for(float v:r.scores)need(std::isfinite(v),"Timing score nonfinite");
    for(float v:r.poses)need(std::isfinite(v),"Timing pose nonfinite");
    need(std::memcmp(r.input.data(),c.input.data(),sizeof(r.input))==0,"Timing actual input differs");
    need(std::memcmp(r.scores.data(),c.scores.data(),sizeof(r.scores))==0&&std::memcmp(r.poses.data(),c.poses.data(),sizeof(r.poses))==0,"Timing actual model output differs");
}
void save(const std::vector<Measurement>& records,const std::vector<pose::validation::FixtureWindow>& cases,const std::filesystem::path& out){
    std::ofstream timings(out/"timing.jsonl"),calls(out/"inference.jsonl");
    need(bool(timings)&&bool(calls),"Timing evidence open failed");timings<<std::setprecision(17);
    for(size_t i=0;i<records.size();++i){const auto& v=records[i];auto c=fixtureFor(cases,v.item.window.frame_id);const auto fixtureId=c.window.frame_id;c.window.frame_id=v.item.window.frame_id;
        const auto& r=v.result;
        timings<<"{\"invocation\":"<<i<<",\"transport_id\":"<<v.item.window.frame_id<<",\"sequence\":"<<v.item.sequence<<",\"case\":\""<<c.name<<"\",\"fixture_frame_id\":"<<fixtureId
        <<",\"arrived_ns\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(v.item.arrived.time_since_epoch()).count()<<",\"dequeued_ns\":"<<v.dequeued<<",\"process_begin_ns\":"<<v.processBegin<<",\"process_end_ns\":"<<v.processEnd
        <<",\"verify_end_ns\":"<<v.verifyEnd<<",\"draw_end_ns\":"<<v.drawEnd<<",\"convert_end_ns\":"<<v.convertEnd<<",\"published_ns\":"<<v.published
        <<",\"preprocess_ms\":"<<r.preprocess_ms<<",\"prepare_ms\":"<<r.prepare_ms<<",\"state_clear_ms\":"<<r.state_clear_ms<<",\"forward_ms\":"<<r.forward_ms<<",\"final_wait_ms\":"<<r.final_wait_ms<<",\"output_ms\":"<<r.output_ms<<",\"selection_ms\":"<<r.selection_ms<<",\"process_ms\":"<<r.process_ms<<"}\n";
        timings.flush();need(bool(timings),"Timing write failed");
        pose::validation::saveThenVerifyResult(c,r,v.item.window,i,out,calls);
    }
}
}
