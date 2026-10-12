#include "owned_result_save.hpp"
#include <iomanip>
#include <stdexcept>
namespace pose::owned_results {
namespace {void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}}
void saveReturned(const pose::measurement::Measurement& v,size_t i,const std::filesystem::path& out){
    need(i<103,"Owned result invocation bound");const auto parent=out/"presaved-results";
    if(!std::filesystem::exists(parent))std::filesystem::create_directory(parent);
    const auto dir=parent/std::to_string(i);need(!std::filesystem::exists(dir),"Preserve returned result");std::filesystem::create_directory(dir);
    const auto&r=v.result;pose::validation::persistBytes(dir/"input.f32",r.input.data(),sizeof(r.input));
    pose::validation::persistBytes(dir/"scores.f32",r.scores.data(),sizeof(r.scores));pose::validation::persistBytes(dir/"poses.f32",r.poses.data(),sizeof(r.poses));
    pose::validation::persistBytes(dir/"raw-payload.bin",v.item.window.csi.data(),sizeof(v.item.window.csi));
    std::ofstream f(dir/"identity.json");f<<"{\"saved_before_gate\":true,\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation<<",\"serializer_compared_math\":false}\n";need(bool(f),"Returned identity write failed");
}
void save(const std::vector<pose::measurement::Measurement>& records,const std::vector<pose::validation::FixtureWindow>& cases,const std::filesystem::path& out){
    need(records.size()<=103,"Owned result record bound");
    for(const char* name:{"timing.jsonl","inference.jsonl","owned-result-index.json"})need(!std::filesystem::exists(out/name),"Preserve owned result ledger");
    std::ofstream timings(out/"timing.jsonl"),calls(out/"inference.jsonl");
    need(bool(timings)&&bool(calls),"Timing evidence open failed");timings<<std::setprecision(17);
    for(size_t i=0;i<records.size();++i){const auto& v=records[i];auto c=pose::measurement::fixtureFor(cases,v.item.window.frame_id);const auto fixtureId=c.window.frame_id;c.window.frame_id=v.item.window.frame_id;
        const auto& r=v.result;
        timings<<"{\"invocation\":"<<i<<",\"transport_id\":"<<v.item.window.frame_id<<",\"sequence\":"<<v.item.sequence<<",\"case\":\""<<c.name<<"\",\"fixture_frame_id\":"<<fixtureId
        <<",\"arrived_ns\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(v.item.arrived.time_since_epoch()).count()<<",\"dequeued_ns\":"<<v.dequeued<<",\"process_begin_ns\":"<<v.processBegin<<",\"process_end_ns\":"<<v.processEnd
        <<",\"verify_end_ns\":"<<v.verifyEnd<<",\"draw_end_ns\":"<<v.drawEnd<<",\"convert_end_ns\":"<<v.convertEnd<<",\"published_ns\":"<<v.published
        <<",\"preprocess_ms\":"<<r.preprocess_ms<<",\"prepare_ms\":"<<r.prepare_ms<<",\"state_clear_ms\":"<<r.state_clear_ms<<",\"forward_ms\":"<<r.forward_ms<<",\"final_wait_ms\":"<<r.final_wait_ms<<",\"output_ms\":"<<r.output_ms<<",\"selection_ms\":"<<r.selection_ms<<",\"process_ms\":"<<r.process_ms<<"}\n";
        timings.flush();need(bool(timings),"Timing write failed");
        const auto stem="result"+std::to_string(i);
        for(const char* suffix:{".input.f32",".scores.f32",".poses.f32",".raw-payload.bin"})need(!std::filesystem::exists(out/(stem+suffix)),"Preserve owned result bytes");
        pose::validation::persistBytes(out/(stem+".input.f32"),r.input.data(),sizeof(r.input));
        pose::validation::persistBytes(out/(stem+".scores.f32"),r.scores.data(),sizeof(r.scores));
        pose::validation::persistBytes(out/(stem+".poses.f32"),r.poses.data(),sizeof(r.poses));
        pose::validation::persistBytes(out/(stem+".raw-payload.bin"),v.item.window.csi.data(),sizeof(v.item.window.csi));
        calls<<std::setprecision(17)<<"{\"call\":"<<i<<",\"case\":"<<std::quoted(c.name)<<",\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation
        <<",\"before_forward\":"<<r.before_forward<<",\"completed_layers\":"<<r.completed_layers<<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks<<",\"best_index\":"<<r.best_index<<",\"process_ms\":"<<r.process_ms<<",\"runtime_gate_completed\":"<<(v.verifyEnd?"true":"false")<<"}"<<std::endl;
        need(bool(calls),"Owned result trace write failed");
    }
    std::ofstream index(out/"owned-result-index.json");index<<"{\"count\":"<<records.size()<<",\"serializer_compared_math\":false,\"includes_unverified_values\":true}\n";need(bool(index),"Owned result index write failed");
}
}
