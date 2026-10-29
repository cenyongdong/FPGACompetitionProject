#pragma once
#include "wire.hpp"
#include <atomic>
#include <array>
#include <chrono>
#include <deque>
#include <mutex>
#include <optional>
#include <string>
#include <vector>

namespace pose180_demo {
namespace pp = pose180_pipeline;
inline std::uint64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}
// Values are copied under a short lock. Consumers own their copy; replacing
// pending work can never overwrite a running SDK call or a partial TCP send.
template<class T> class Latest {
    mutable std::mutex mutex_;
    std::optional<T> pending_;
public:
    bool put(const T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        const bool replaced = bool(pending_); pending_ = value; return replaced;
    }
    bool take(T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (!pending_) return false;
        value = std::move(*pending_); pending_.reset(); return true;
    }
    void clear() { std::lock_guard<std::mutex> lock(mutex_); pending_.reset(); }
};
struct Input {
    pp::Window window;
    std::uint64_t epoch=0, arrived=0;
};
using Record = std::array<unsigned char, pp::full_bytes>;
struct Stats {
    // Set before worker construction; provenance only, never a display label.
    std::string input_source="tcp_window";
    std::optional<float> score_threshold=0.2f;
    unsigned top_k=3;
    bool single_person_stability=false;
    std::atomic<std::uint64_t> single_rejected{0},single_relocations{0},single_limited{0};
    std::atomic<bool> dataset_done{false};
    std::atomic<std::uint64_t> dataset_passes{0};
    std::atomic<std::uint64_t> received{0}, replaced{0}, stale{0}, malformed{0}, reconnects{0};
    std::atomic<std::uint64_t> inferred{0}, adopted{0}, pc_sent{0}, pc_dropped{0};
    std::atomic<std::uint64_t> view_sent{0},view_dropped{0};
    std::atomic<std::uint64_t> post_frames{0},post_ns{0},post_max_ns{0},post_births{0},post_duplicates{0},post_display_duplicates{0},post_resets{0};
    std::atomic<std::uint64_t> post_history_selections{0},post_reacquired{0},post_held_handoffs{0},post_hidden_frames{0},post_shadow_deferred{0};
    std::atomic<std::uint64_t> filter_lanes{0},filter_fallbacks{0};
    std::atomic<std::uint64_t> cpu_filter_frames{0},cpu_filter_coordinates{0},cpu_filter_ns{0},cpu_filter_max_ns{0};
    std::atomic<std::uint64_t> pl_filter_calls{0},pl_filter_coordinates{0},pl_input_ns{0},pl_wait_ns{0},pl_output_ns{0},pl_total_ns{0},pl_max_ns{0},pl_compute_cycles{0},pl_max_cycles{0};
    std::atomic<std::uint64_t> pl_geometry_calls{0},pl_geometry_input_ns{0},pl_geometry_wait_ns{0},pl_geometry_output_ns{0},pl_geometry_total_ns{0},pl_geometry_max_ns{0},pl_geometry_cycles{0};
    std::atomic<std::uint64_t> ps_reference_frames{0},ps_reference_ns{0},ps_reference_max_ns{0},ps_reference_filter_frames{0},ps_reference_filter_ns{0},ps_reference_filter_max_ns{0},ps_reference_filter_coordinates{0},reference_mismatch_frames{0},reference_max_error_nano{0};
    std::atomic<std::uint64_t> joint_gate_rejections{0},bone_gate_rejections{0};
    std::atomic<std::uint64_t> record_dropped{0}, input_epoch{0}, last_input{0}, last_result{0}, last_adopt{0};
    std::atomic<std::uint64_t> forward_start{0}, longest_gap{0}, resyncs{0};
    std::atomic<std::uint64_t> display_updates{0}, display_hints{0};
    std::atomic<std::uint64_t> selected_count{0};
    std::array<std::atomic<std::uint64_t>,4> selection_counts{};
    std::atomic<std::uint64_t> alignment_resets{0}, transport_resets{0}, diagnostic_dropped{0};
    std::atomic<std::uint64_t> last_recovery_ms{0}, longest_recovery_ms{0};
    std::atomic<bool> adaptive_csi{false};
    std::atomic<std::uint64_t> csi_exact_windows{0},csi_approximate_windows{0},csi_approximate_points{0};
    std::atomic<std::uint64_t> csi_mapping_switches{0},csi_skipped_points{0},csi_decoder_resets{0};
    std::atomic<std::uint64_t> csi_max_skew_us{0},csi_max_span_us{0},longest_input_gap{0};
    std::atomic<std::uint64_t> csi_rejected_records{0};
    std::atomic<bool> isolated{false}, recording{true}, input_connected{false}, pc_connected{false};
    std::atomic<bool> release_blocked{false};
    std::atomic<bool> initialized{false}, resynchronizing{false};
    mutable std::mutex input_error_mutex;
    std::string last_input_error;
    std::mutex input_events_mutex;
    std::deque<std::string> input_events;
    void input_event(std::string event) {
        std::lock_guard<std::mutex> lock(input_events_mutex);
        if(event.size()>1024){++diagnostic_dropped;return;}
        if(input_events.size()==16){input_events.pop_front();++diagnostic_dropped;}
        input_events.push_back(std::move(event));
    }
    std::vector<std::string> take_input_events() {
        std::lock_guard<std::mutex> lock(input_events_mutex);
        std::vector<std::string> result;
        while(!input_events.empty()){result.push_back(std::move(input_events.front()));input_events.pop_front();}
        return result;
    }
    void input_error(const char* message) {
        std::lock_guard<std::mutex> lock(input_error_mutex);
        last_input_error=std::string(message).substr(0,160);
    }
    std::string json(bool mock, bool hdmi) const;
};
inline std::string Stats::json(bool mock, bool hdmi) const {
    const auto now=now_ns();
    // A worker may publish a newer timestamp after this status snapshot starts.
    // Clamp that concurrent update instead of wrapping an unsigned subtraction.
    auto elapsed=[&](std::uint64_t t){return now>t?now-t:0;};
    auto age=[&](std::uint64_t t){return t ? std::to_string(elapsed(t)/1000000) : "null";};
    const auto last=last_result.load(), busy=forward_start.load();
    const char* state=release_blocked ? "release_blocked" : isolated ? "isolated" : !initialized ? "initializing" :
        resynchronizing ? "resynchronizing" : busy && elapsed(busy)>1000000000 ? "degraded" :
        !last || elapsed(last)>2000000000 ? "waiting_input" : "running";
    std::string s="{\"state\":\""+std::string(state)+"\",\"mock\":"+(mock?"true":"false")+
        ",\"hdmi\":"+(hdmi?"true":"false")+",\"input_source\":\""+input_source+"\",\"dataset_done\":"+(dataset_done?"true":"false");
    s+=",\"score_threshold\":"+(score_threshold?std::to_string(*score_threshold):std::string("null"));
    s+=",\"top_k\":"+std::to_string(top_k);
    s+=",\"single_person_stability\":"+std::string(single_person_stability?"true":"false");
    s+=",\"release_blocked\":"+std::string(release_blocked?"true":"false");
    auto add=[&](const char* k,std::uint64_t v){s+=",\""+std::string(k)+"\":"+std::to_string(v);};
    add("single_rejected",single_rejected);add("single_relocations",single_relocations);add("single_limited",single_limited);
    add("received",received);add("replaced",replaced);add("stale",stale);add("malformed",malformed);
    add("dataset_passes",dataset_passes);
    add("reconnects",reconnects);add("input_epoch",input_epoch);add("inferred",inferred);add("adopted",adopted);
    add("pc_sent",pc_sent);add("pc_dropped",pc_dropped);add("record_dropped",record_dropped);add("resyncs",resyncs);
    add("view_sent",view_sent);add("view_dropped",view_dropped);
    add("post_frames",post_frames);add("post_total_us",post_ns.load()/1000);add("post_max_us",post_max_ns.load()/1000);
    add("post_births",post_births);add("post_duplicates",post_duplicates);add("post_display_duplicates",post_display_duplicates);add("post_resets",post_resets);
    add("post_history_selections",post_history_selections);add("post_reacquired",post_reacquired);add("post_held_handoffs",post_held_handoffs);add("post_hidden_frames",post_hidden_frames);
    add("post_shadow_deferred",post_shadow_deferred);
    add("filter_lanes",filter_lanes);add("filter_fallbacks",filter_fallbacks);
    add("cpu_filter_frames",cpu_filter_frames);add("cpu_filter_coordinates",cpu_filter_coordinates);
    add("cpu_filter_total_ns",cpu_filter_ns);add("cpu_filter_max_ns",cpu_filter_max_ns);
    add("pl_filter_calls",pl_filter_calls);add("pl_filter_coordinates",pl_filter_coordinates);
    add("pl_geometry_calls",pl_geometry_calls);add("pl_geometry_input_ns",pl_geometry_input_ns);add("pl_geometry_wait_ns",pl_geometry_wait_ns);add("pl_geometry_output_ns",pl_geometry_output_ns);add("pl_geometry_total_ns",pl_geometry_total_ns);add("pl_geometry_max_ns",pl_geometry_max_ns);add("pl_geometry_cycles",pl_geometry_cycles);
    add("ps_reference_frames",ps_reference_frames);add("ps_reference_ns",ps_reference_ns);add("ps_reference_max_ns",ps_reference_max_ns);add("ps_reference_filter_frames",ps_reference_filter_frames);add("ps_reference_filter_ns",ps_reference_filter_ns);add("ps_reference_filter_max_ns",ps_reference_filter_max_ns);add("ps_reference_filter_coordinates",ps_reference_filter_coordinates);add("reference_mismatch_frames",reference_mismatch_frames);add("reference_max_error_nano",reference_max_error_nano);
    add("joint_gate_rejections",joint_gate_rejections);add("bone_gate_rejections",bone_gate_rejections);
    add("pl_input_ns",pl_input_ns);add("pl_wait_ns",pl_wait_ns);add("pl_output_ns",pl_output_ns);
    add("pl_total_ns",pl_total_ns);add("pl_max_ns",pl_max_ns);add("pl_compute_cycles",pl_compute_cycles);add("pl_max_cycles",pl_max_cycles);
    add("longest_result_gap_ms",longest_gap.load()/1000000);
    add("display_updates",display_updates);add("display_hints",display_hints);
    add("selected_count",selected_count);
    for(unsigned i=0;i<selection_counts.size();++i)
        add(("selected_"+std::to_string(i)+"_frames").c_str(),selection_counts[i]);
    add("alignment_resets",alignment_resets);add("transport_resets",transport_resets);
    add("diagnostic_dropped",diagnostic_dropped);add("last_recovery_ms",last_recovery_ms);
    add("longest_recovery_ms",longest_recovery_ms);
    s+=",\"csi_alignment\":\""+std::string(input_source=="live_csi"?(adaptive_csi?"adaptive":"strict"):"none")+"\"";
    add("csi_exact_windows",csi_exact_windows);add("csi_approximate_windows",csi_approximate_windows);
    add("csi_approximate_points",csi_approximate_points);add("csi_mapping_switches",csi_mapping_switches);
    add("csi_skipped_points",csi_skipped_points);add("csi_decoder_resets",csi_decoder_resets);
    add("csi_max_skew_us",csi_max_skew_us);add("csi_max_span_us",csi_max_span_us);
    add("csi_rejected_records",csi_rejected_records);
    add("longest_input_gap_ms",longest_input_gap.load()/1000000);
    std::string reason;
    {std::lock_guard<std::mutex> lock(input_error_mutex);
        for(unsigned char c:last_input_error){if(c=='"'||c=='\\')reason+='\\';if(c>=32)reason+=c;}}
    s+=",\"last_input_error\":\""+reason+"\",\"input_age_ms\":"+age(last_input)+",\"result_age_ms\":"+age(last)+
       ",\"adoption_age_ms\":"+age(last_adopt)+",\"forward_age_ms\":"+age(busy)+
       ",\"recording\":"+(recording?"true":"false")+",\"pc_connected\":"+(pc_connected?"true":"false")+
       ",\"input_connected\":"+(input_connected?"true":"false")+"}\n";
    return s;
}
struct Shared {
    Latest<Input> input;
    Latest<Record> output;
    Latest<std::string> presentation;
    Stats stats;
    std::atomic<bool> stop{false};
};
inline void accept_input(Shared& shared, const Input& input) {
    if(shared.stats.isolated) return;
    if(shared.input.put(input)) ++shared.stats.replaced;
    ++shared.stats.received;
    const auto previous=shared.stats.last_input.exchange(input.arrived);
    if(previous&&input.arrived>=previous)
        shared.stats.longest_input_gap=std::max(shared.stats.longest_input_gap.load(),input.arrived-previous);
}
} // namespace pose180_demo
