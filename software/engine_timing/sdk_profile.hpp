// 仅通过公开SDK采样；在Engine process返回后、下一reset之前调用。
#pragma once

#include <icraft-xrt/core/session.h>
#include <icraft-xrt/dev/zg330_device.h>
#include <chrono>
#include <cmath>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <map>
#include <tuple>
#include <vector>

namespace pose_v1::timing_sdk {
    struct Snapshot {
        uint64_t frame = 0, invocation = 0;
        double collection_ms = 0, session_total_ms = 0;
        std::map<int64_t, std::tuple<double, double, double, double>> operators;
        std::vector<double> layer_ms;
    };
    inline bool enabled = false;
    inline std::vector<Snapshot> snapshots;

    inline void configure(bool value) {
        enabled = value;
        snapshots.reserve(32);
    }

    inline void collect(const icraft::xrt::Session& session, icraft::xrt::Device device,
                        uint64_t frame, uint64_t invocation) {
        if (!enabled) return;
        if (snapshots.size() >= 32) throw std::runtime_error("SDK profile budget exceeded");
        const auto begin = std::chrono::steady_clock::now();
        Snapshot result;
        result.frame = frame;
        result.invocation = invocation;
        for (const auto& item : session.timeProfileResults()) result.operators.emplace(item.first, item.second);
        result.session_total_ms = session.totalTime<std::chrono::milliseconds>();
        // getLayerTime公开说明单位为ms；不读私有timer地址或猜测寄存器。
        result.layer_ms = device.cast<icraft::xrt::ZG330Device>().getLayerTime(745);
        result.collection_ms = std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - begin).count();
        // 先保存原返回，再验证；SDK语义或容量不符时停止，不假造缺失值。
        snapshots.push_back(std::move(result));
        const auto& last = snapshots.back();
        if (last.operators.empty() || last.layer_ms.size() != 745) {
            throw std::runtime_error("SDK profile cardinality unverified; original sample retained");
        }
        auto valid = [](double x) { return std::isfinite(x) && x >= 0; };
        if (!valid(last.session_total_ms)) throw std::runtime_error("Invalid SDK total time");
        for (double x : last.layer_ms) if (!valid(x)) throw std::runtime_error("Invalid SDK layer time");
        for (const auto& item : last.operators) {
            if (!valid(std::get<0>(item.second)) || !valid(std::get<1>(item.second)) ||
                !valid(std::get<2>(item.second)) || !std::isfinite(std::get<3>(item.second))) {
                throw std::runtime_error("Invalid SDK time profile");
            }
        }
    }

    inline void number(std::ostream& out, double value) {
        if (std::isfinite(value)) out << value; else out << "null";
    }

    inline void save(const std::filesystem::path& directory) {
        std::ofstream ops(directory / "sdk-profile.jsonl"), layers(directory / "hardware-layers.jsonl");
        ops << std::setprecision(17);
        layers << std::setprecision(17);
        for (const auto& s : snapshots) {
            for (const auto& item : s.operators) {
                ops << "{\"frame_id\":" << s.frame << ",\"invocation\":" << s.invocation
                    << ",\"op_id\":" << item.first << ",\"wall_raw\":";
                number(ops, std::get<0>(item.second));
                ops << ",\"copy_raw\":"; number(ops, std::get<1>(item.second));
                ops << ",\"hardware_raw\":"; number(ops, std::get<2>(item.second));
                ops << ",\"other_raw\":"; number(ops, std::get<3>(item.second));
                ops << ",\"unit\":\"SDK_raw_unconfirmed\",\"aggregation\":\"SDK_unspecified\"}\n";
            }
            layers << "{\"frame_id\":" << s.frame << ",\"invocation\":" << s.invocation
                   << ",\"requested_count\":745,\"unit\":\"ms\",\"collection_ms\":";
            number(layers, s.collection_ms);
            layers << ",\"session_total_ms\":"; number(layers, s.session_total_ms);
            layers << ",\"pure_compute_separated\":false,\"layer_ordinal_mapping_verified\":false,\"values\":[";
            for (size_t i = 0; i < s.layer_ms.size(); ++i) {
                if (i) layers << ',';
                number(layers, s.layer_ms[i]);
            }
            layers << "]}\n";
        }
        if (!ops || !layers) throw std::runtime_error("SDK profile write failed");
    }
}
