// 独立诊断包替换的计时头；正式核心的同名文件保持不变。
// 墙钟、线程CPU与缺页/切换只观测宿主线程，不代表NPU内部状态。
#pragma once

#include <chrono>
#include <cstdint>
#include <exception>
#include <filesystem>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <thread>
#include <vector>
#ifdef __linux__
#include <sys/resource.h>
#include <time.h>
#endif

namespace pose_v1::forward_clock {
    using Clock = std::chrono::steady_clock;

    struct Sample {
        Clock::time_point wall;
        int64_t cpu_ns = 0, minor_faults = 0, major_faults = 0;
        int64_t voluntary_switches = 0, involuntary_switches = 0;
        bool cpu_valid = false, usage_valid = false;
    };

    struct Record {
        const char* kind;
        int64_t op, slot;
        uint64_t frame, invocation;
        int64_t begin, end;
        Sample first, last;
        bool failed = false;
    };

    struct Transfer {
        const char* kind;
        const char* direction;
        int64_t op, slot;
        uint64_t frame, invocation, bytes;
    };

    inline std::mutex mutex;
    inline bool active = false, overflow = false, invalid_thread = false;
    inline size_t sample_limit = 0;
    inline constexpr size_t record_limit = 8192;
    inline Clock::time_point epoch;
    inline uint64_t frame = 0, invocation = 0;
    inline std::thread::id owner;
    inline std::vector<Record> records;
    inline std::vector<Transfer> transfers;

    // 在Engine创建前预留容量，热路径不落盘，不动态扩大采样预算。
    inline void configure(size_t frames) {
        if (frames > 32 || !records.empty()) throw std::runtime_error("Invalid timing configuration");
        owner = std::this_thread::get_id();
        sample_limit = frames;
        records.reserve(record_limit);
        transfers.reserve(1024);
    }

    inline Sample sample() noexcept {
        Sample s;
        s.wall = Clock::now();
        if (!active) return s;
#ifdef __linux__
        timespec time{};
        if (clock_gettime(CLOCK_THREAD_CPUTIME_ID, &time) == 0) {
            s.cpu_ns = int64_t(time.tv_sec) * 1000000000 + time.tv_nsec;
            s.cpu_valid = true;
        }
        rusage usage{};
        if (getrusage(RUSAGE_THREAD, &usage) == 0) {
            s.minor_faults = usage.ru_minflt;
            s.major_faults = usage.ru_majflt;
            s.voluntary_switches = usage.ru_nvcsw;
            s.involuntary_switches = usage.ru_nivcsw;
            s.usage_valid = true;
        }
#endif
        return s;
    }

    inline void begin_initialization() {
        epoch = Clock::now();
        frame = 0;
        invocation = UINT64_MAX;
        active = sample_limit > 0;
    }

    inline void start(uint64_t f, uint64_t i, Clock::time_point t) {
        std::lock_guard<std::mutex> guard(mutex);
        if (std::this_thread::get_id() != owner) {
            invalid_thread = true;
            throw std::runtime_error("Timing owner thread changed");
        }
        frame = f;
        invocation = i;
        epoch = t;
        active = i < sample_limit;
    }

    inline void record(const char* kind, int64_t op, int64_t slot,
                       Clock::time_point a, Clock::time_point b,
                       Sample first = {}, Sample last = {}, bool failed = false) noexcept {
        try {
            std::lock_guard<std::mutex> guard(mutex);
            if (!active) return;
            if (std::this_thread::get_id() != owner) { invalid_thread = true; return; }
            if (records.size() == record_limit) { overflow = true; return; }
            auto ns = [](Clock::time_point t) {
                return std::chrono::duration_cast<std::chrono::nanoseconds>(t - epoch).count();
            };
            records.push_back({kind, op, slot, frame, invocation, ns(a), ns(b), first, last, failed});
        } catch (...) {
            overflow = true;
        }
    }

    inline void record(const char* kind, int64_t op, int64_t slot,
                       const Sample& a, const Sample& b) noexcept {
        record(kind, op, slot, a.wall, b.wall, a, b);
    }

    inline void transfer(const char* kind, int64_t op, int64_t slot,
                         uint64_t bytes, const char* direction) noexcept {
        try {
            if (!active) return;
            if (std::this_thread::get_id() != owner) { invalid_thread = true; return; }
            if (transfers.size() == 1024) { overflow = true; return; }
            transfers.push_back({kind, direction, op, slot, frame, invocation, bytes});
        } catch (...) { overflow = true; }
    }

    class Span {
        const char* kind_;
        int64_t op_, slot_;
        Sample begin_;
        int exceptions_;
    public:
        Span(const char* k, int64_t o = 0, int64_t s = 0)
            : kind_(k), op_(o), slot_(s), begin_(sample()), exceptions_(std::uncaught_exceptions()) {}
        ~Span() noexcept {
            const auto end = sample();
            record(kind_, op_, slot_, begin_.wall, end.wall, begin_, end,
                   std::uncaught_exceptions() > exceptions_);
        }
    };

    inline void check() {
        if (overflow || invalid_thread) throw std::runtime_error("Timing trace incomplete; stop without extrapolation");
    }

    inline void save(const std::filesystem::path& path) {
        std::lock_guard<std::mutex> guard(mutex);
        std::ofstream out(path);
        if (!out) throw std::runtime_error("Cannot save timing evidence");
        for (const auto& r : records) {
            const bool cpu = r.first.cpu_valid && r.last.cpu_valid;
            const bool usage = r.first.usage_valid && r.last.usage_valid;
            out << "{\"kind\":\"" << r.kind << "\",\"op_id\":" << r.op << ",\"slot\":" << r.slot
                << ",\"frame_id\":" << r.frame << ",\"invocation\":" << r.invocation
                << ",\"begin_ns\":" << r.begin << ",\"end_ns\":" << r.end
                << ",\"failed\":" << (r.failed ? "true" : "false") << ",\"cpu_begin_ns\":";
            if (cpu) out << r.first.cpu_ns; else out << "null";
            out << ",\"cpu_end_ns\":";
            if (cpu) out << r.last.cpu_ns; else out << "null";
            out << ",\"thread_cpu_ns\":";
            if (cpu) out << r.last.cpu_ns - r.first.cpu_ns; else out << "null";
            auto delta = [&](const char* name, int64_t a, int64_t b) {
                out << ",\"" << name << "\":";
                if (usage) out << b - a; else out << "null";
            };
            delta("minor_faults", r.first.minor_faults, r.last.minor_faults);
            delta("major_faults", r.first.major_faults, r.last.major_faults);
            delta("voluntary_switches", r.first.voluntary_switches, r.last.voluntary_switches);
            delta("involuntary_switches", r.first.involuntary_switches, r.last.involuntary_switches);
            out << "}\n";
        }
        if (!out) throw std::runtime_error("Timing write failed");
        // 先保存已有证据，再报告丢失；不因异常掩盖部分记录。
        check();
    }

    inline void save_transfers(const std::filesystem::path& path) {
        std::ofstream out(path);
        for (const auto& t : transfers) {
            out << "{\"kind\":\"" << t.kind << "\",\"direction\":\"" << t.direction
                << "\",\"op_id\":" << t.op << ",\"slot\":" << t.slot
                << ",\"frame_id\":" << t.frame << ",\"invocation\":" << t.invocation
                << ",\"logical_bytes\":" << t.bytes << "}\n";
        }
        if (!out) throw std::runtime_error("Transfer metadata write failed");
    }
}
