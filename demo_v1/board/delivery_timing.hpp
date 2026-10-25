#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace demo_v1 {
    // 仅记录普通内存中的时间线；热路径不写文件。每线程一条当前记录，失败仍可保存。
    struct DeliveryRow {
        uint64_t invocation=0, sequence=0, dequeued=0, encode_end=0, send_begin=0, send_end=0;
        uint64_t ack_begin=0, ack_end=0, gate_end=0, confirm_end=0;
    };
    struct PressureRow { uint64_t invocation=0, begin=0, end=0; size_t depth=0; };
    class DeliveryTiming {
        std::array<DeliveryRow,256> rows_{};
        std::array<PressureRow,256> pressure_{};
        size_t count_=0, pressure_count_=0;
        uint64_t send_max_=0, ack_max_=0, pressure_max_=0, blocked_=0;
        size_t capacity_;
    public:
        explicit DeliveryTiming(size_t capacity):capacity_(capacity){}
        DeliveryRow& begin(uint64_t invocation, uint64_t sequence, uint64_t now) {
            auto& r=rows_[count_++%rows_.size()]; r={};r.invocation=invocation;r.sequence=sequence;r.dequeued=now;return r;
        }
        void done(const DeliveryRow& r) {
            send_max_=std::max(send_max_,r.send_end-r.send_begin);ack_max_=std::max(ack_max_,r.ack_end-r.ack_begin);
        }
        void pressure(uint64_t invocation,uint64_t begin,uint64_t end,size_t depth) {
            const auto elapsed=end-begin;
            if(elapsed>=1000000) {++blocked_;pressure_[pressure_count_++%pressure_.size()]={invocation,begin,end,depth};}
            pressure_max_=std::max(pressure_max_,elapsed);
        }
        // 仅在线程join后调用。
        void save(const std::filesystem::path& root) const {
            std::ofstream f(root/"delivery-timing.jsonl");
            for(size_t n=count_>rows_.size()?count_-rows_.size():0;n<count_;++n) {
                const auto& r=rows_[n%rows_.size()];
                f<<"{\"invocation\":"<<r.invocation<<",\"sequence\":"<<r.sequence<<",\"dequeued_ns\":"<<r.dequeued
                 <<",\"encode_end_ns\":"<<r.encode_end<<",\"send_begin_ns\":"<<r.send_begin<<",\"send_end_ns\":"<<r.send_end
                 <<",\"ack_begin_ns\":"<<r.ack_begin<<",\"ack_end_ns\":"<<r.ack_end<<",\"gate_end_ns\":"<<r.gate_end
                 <<",\"confirm_end_ns\":"<<r.confirm_end<<"}\n";
            }
            for(size_t n=pressure_count_>pressure_.size()?pressure_count_-pressure_.size():0;n<pressure_count_;++n) {
                const auto& r=pressure_[n%pressure_.size()];
                f<<"{\"kind\":\"output_backpressure\",\"invocation\":"<<r.invocation<<",\"begin_ns\":"<<r.begin
                 <<",\"end_ns\":"<<r.end<<",\"depth\":"<<r.depth<<"}\n";
            }
            f.close();if(!f)throw std::runtime_error("Delivery timing save failed");
            std::ofstream s(root/"delivery-summary.json");
            s<<"{\"publisher_started\":"<<count_<<",\"max_send_ns\":"<<send_max_<<",\"max_ack_wait_ns\":"<<ack_max_
             <<",\"output_waits_over_1ms\":"<<blocked_<<",\"max_output_wait_ns\":"<<pressure_max_<<",\"capacity\":"<<capacity_<<",\"backpressure_limit_ms\":1000}\n";
            s.close();if(!s)throw std::runtime_error("Delivery summary save failed");
        }
    };
}
