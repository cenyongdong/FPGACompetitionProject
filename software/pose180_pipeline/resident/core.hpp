#pragma once
#include "wire.hpp"
#include <atomic>
#include <chrono>
#include <mutex>
#include <optional>
#include <string>

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
    std::atomic<std::uint64_t> received{0}, replaced{0}, stale{0}, malformed{0}, reconnects{0};
    std::atomic<std::uint64_t> inferred{0}, adopted{0}, pc_sent{0}, pc_dropped{0};
    std::atomic<std::uint64_t> record_dropped{0}, input_epoch{0}, last_input{0}, last_result{0}, last_adopt{0};
    std::atomic<std::uint64_t> forward_start{0}, longest_gap{0}, resyncs{0};
    std::atomic<bool> isolated{false}, recording{true}, input_connected{false}, pc_connected{false};
    std::atomic<bool> initialized{false}, resynchronizing{false};
    mutable std::mutex input_error_mutex;
    std::string last_input_error;
    void input_error(const char* message) {
        std::lock_guard<std::mutex> lock(input_error_mutex);
        last_input_error=std::string(message).substr(0,160);
    }
    std::string json(bool mock, bool hdmi) const;
};
inline std::string Stats::json(bool mock, bool hdmi) const {
    const auto now=now_ns();
    auto age=[&](std::uint64_t t){return t ? std::to_string((now-t)/1000000) : "null";};
    const auto last=last_result.load(), busy=forward_start.load();
    const char* state=isolated ? "isolated" : !initialized ? "initializing" :
        resynchronizing ? "resynchronizing" : busy && now-busy>1000000000 ? "degraded" :
        !last || now-last>2000000000 ? "waiting_input" : "running";
    std::string s="{\"state\":\""+std::string(state)+"\",\"mock\":"+(mock?"true":"false")+
        ",\"hdmi\":"+(hdmi?"true":"false");
    auto add=[&](const char* k,std::uint64_t v){s+=",\""+std::string(k)+"\":"+std::to_string(v);};
    add("received",received);add("replaced",replaced);add("stale",stale);add("malformed",malformed);
    add("reconnects",reconnects);add("input_epoch",input_epoch);add("inferred",inferred);add("adopted",adopted);
    add("pc_sent",pc_sent);add("pc_dropped",pc_dropped);add("record_dropped",record_dropped);add("resyncs",resyncs);
    add("longest_result_gap_ms",longest_gap.load()/1000000);
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
    Stats stats;
    std::atomic<bool> stop{false};
};
inline void accept_input(Shared& shared, const Input& input) {
    if(shared.stats.isolated) return;
    if(shared.input.put(input)) ++shared.stats.replaced;
    ++shared.stats.received; shared.stats.last_input=input.arrived;
}
} // namespace pose180_demo
