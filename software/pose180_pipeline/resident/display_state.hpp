#pragma once
#include "hdmi_renderer.hpp"
#include <cstdint>
#include <optional>
#include <stdexcept>

namespace pose180_demo {
// Pure owner-thread presentation state. No SDK, clocks, IO or background work.
// A successful hint adoption is deliberately distinct from a new model result.
class DisplayState {
    using Notice = pose::hdmi::Notice;
    using Kind = pose::hdmi::NoticeKind;
    bool has_result_ = false, has_shown_ = false;
    std::uint64_t last_result_ = 0, last_update_ = 0;
    std::uint64_t updates_ = 0, hints_ = 0;
    std::uint32_t tag_ = 0;
    Notice shown_{};
public:
    static constexpr std::uint64_t short_gap_ns = 750000000;
    static constexpr std::uint64_t hint_interval_ns = 1000000000;
    static constexpr std::uint64_t stale_ns = 2000000000;

    // Keep submission identities independent of inference/source frame IDs.
    // Stop before rollover; never recycle a live hardware tag.
    std::uint32_t next_tag() {
        if (tag_ == 0x6fffffffu) throw std::runtime_error("HDMI submission tag exhausted");
        return ++tag_;
    }
    std::optional<Notice> hint(std::uint64_t now, bool resynchronizing, bool isolated) const {
        if (isolated) return std::nullopt;
        const auto age = has_result_ && now >= last_result_ ? now-last_result_ : 0;
        if (has_result_ && age < short_gap_ns) return std::nullopt;
        if (has_shown_ && now-last_update_ < hint_interval_ns) return std::nullopt;
        Notice next;
        next.has_result = has_result_;
        next.age_seconds = age/1000000000;
        next.resynchronizing = resynchronizing;
        next.kind = has_result_ && age >= stale_ns ? Kind::Stale :
            resynchronizing ? Kind::Resynchronizing : Kind::WaitingInput;
        if (has_shown_ && next.kind == shown_.kind && next.has_result == shown_.has_result &&
            next.age_seconds == shown_.age_seconds && next.resynchronizing == shown_.resynchronizing)
            return std::nullopt;
        return next;
    }
    // Invoke only after the unchanged poll_show adoption proof has succeeded.
    void adopted_result(std::uint64_t now) {
        has_result_=has_shown_=true;last_result_=last_update_=now;
        shown_={pose::hdmi::NoticeKind::Result,true,false,0};++updates_;
    }
    void adopted_hint(const Notice& notice, std::uint64_t now) {
        shown_=notice;has_shown_=true;last_update_=now;++updates_;++hints_;
    }
    std::uint64_t updates() const { return updates_; }
    std::uint64_t hints() const { return hints_; }
    std::uint64_t results() const { return updates_-hints_; }
};
} // namespace pose180_demo
