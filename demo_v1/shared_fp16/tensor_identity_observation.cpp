// 诊断模块：有界保存原值与公开元数据；诊断失败不替代原计算错误。
// 依赖通过本模块头文件声明；公开接口及异常传播遵循冻结基线。

#include "tensor_identity_observation.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>

namespace pose::tensor_identity {
    namespace {
        void need(bool v, const char* m) {
            if (!v) throw std::runtime_error(m);
        }

        std::unique_ptr<Recorder > recorder;
        uint64_t invocation_limit = UINT64_MAX;
        std::filesystem::path root;
        bool same(const Storage& a, const Storage& b) {
            return a.tensor == b.tensor && a.region == b.region && a.chunk == b.chunk && a.device == b.device && a.address == b.address && a.offset == b.offset && a.capacity == b.capacity && a.bytes == b.bytes && a.ownerMatches == b.ownerMatches && a.declaredMatches == b.declaredMatches && a.kind == b.kind && a.regionKey == b.regionKey && a.type == b.type && a.declaredType == b.declaredType;
        }

        void valid(const Storage& s) {
            need(s.tensor && s.region && s.chunk && s.device && s.address, "Undefined public storage identity");
            need(s.ownerMatches && s.declaredMatches, "Storage owner/declaration mismatch");
            need(s.bytes && s.bytes <= 1048576 && s.offset <= s.capacity && s.bytes <= s.capacity - s.offset, "Identity storage bounds");
            need(s.kind == "CPTR" || s.kind == "ADDR" || s.kind == "BOTH", "Identity pointer kind");
            need(!s.regionKey.empty() && !s.type.empty() && s.type == s.declaredType, "Identity type differs");
        }

        void output(std::ostream& f, const Storage& s) {
            f << "{\"tensor_object\":" << s.tensor << ",\"region_object\":" << s.region << ",\"chunk_object\":" << s.chunk <<
            ",\"device_object\":" << s.device << ",\"address_identity\":" << s.address << ",\"offset\":" << s.offset <<
            ",\"capacity\":" << s.capacity << ",\"bytes\":" << s.bytes << ",\"owner_matches\":" << (s.ownerMatches ? "true" : "false") <<
            ",\"declared_matches\":" << (s.declaredMatches ? "true" : "false") << ",\"pointer\":" << std::quoted(s.kind) <<
            ",\"region_key\":" << std::quoted(s.regionKey) << ",\"actual_type\":" << s.type << ",\"declared_type\":" <<
            s.declaredType << '}';
        }

    }

    void Recorder::sample(uint64_t frame, uint64_t invocation, int64_t op, size_t slot, bool after, Pair p) {
        need(std::this_thread::get_id() == owner_, "Identity owner changed");
        need(rows_.size() < 2048, "Identity row budget");
        need(p.source.type.size() + p.source.declaredType.size() + p.destination.type.size() + p.destination.declaredType.size() <= 16384, "Identity type budget");
        need(total_ <= 4194304 - (p.source.type.size() + p.source.declaredType.size() + p.destination.type.size() + p.destination.declaredType.size() + 1024), "Identity byte budget");
        total_ += p.source.type.size() + p.source.declaredType.size() + p.destination.type.size() + p.destination.declaredType.size() + 1024;
        const auto time = std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();
        Row row { frame, invocation, uint64_t(time), op, slot, after, std::move(p), {} };
        try {
            need((op == 188 || op == 192 || op == 437 || op == 582 || op == 649) && slot < 8, "Identity op/slot differs");
            valid(row.pair.source);
            valid(row.pair.destination);
            need(row.pair.destination.kind == "CPTR", "Identity destination not Host CPTR");
            need(row.pair.source.type == row.pair.destination.type && row.pair.source.bytes == row.pair.destination.bytes, "Identity source/target type differs");
            if (!after) {
                need(!pending_, "Identity previous copy incomplete");
                pending_ = true;
            } else {
                need(pending_ && !rows_.empty(), "Identity after without before");
                const auto& b = rows_.back();
                need(!b.after && b.frame == frame && b.invocation == invocation && b.op == op && b.slot == slot && same(b.pair.source, row.pair.source) && same(b.pair.destination, row.pair.destination) && b.pair.sameRegion == row.pair.sameRegion && b.pair.sameDevice == row.pair.sameDevice, "Identity changed across copy");
                pending_ = false;
            }
        } catch (const std::exception& e) {
            row.error = e.what();
            rows_.push_back(std::move(row));
            throw;
        }

        rows_.push_back(std::move(row));
    }

    void Recorder::save(const std::filesystem::path& out) const {
        need(std::this_thread::get_id() == owner_, "Identity save owner changed");
        need(!out.empty() && !std::filesystem::exists(out), "Preserve identity evidence");
        std::filesystem::create_directory(out);
        std::ofstream f(out / "objects.jsonl");
        for (const auto & r : rows_) {
            f << "{\"frame_id\":" << r.frame << ",\"invocation\":" << r.invocation << ",\"op_id\":" << r.op << ",\"slot\":" <<
            r.slot << ",\"point\":\"" << (r.after ? "after_copy" : "before_copy") << "\",\"time_ns\":" << r.time << ",\"source\":";
            output(f, r.pair.source);
            f << ",\"destination\":";
            output(f, r.pair.destination);
            f << ",\"same_region\":" << (r.pair.sameRegion ? "true" : "false") << ",\"same_device\":" << (r.pair.sameDevice ? "true" : "false") <<
            ",\"error\":" << std::quoted(r.error) << ",\"device_data_read_added\":false}\n";
        }

        f.close();
        need(bool(f), "Identity save failed");
    }

    void configure(const std::filesystem::path& out, uint64_t limit) {
        need(!recorder && !out.empty() && !std::filesystem::exists(out), "Preserve identity configuration");
        root = out;
        invocation_limit = limit;
        recorder = std::make_unique<Recorder>();
    }

    bool enabled() {
        return bool(recorder);
    }

    void sample(uint64_t f, uint64_t i, int64_t op, size_t slot, bool after, Pair p) {
        if (recorder && i < invocation_limit) recorder->sample(f, i, op, slot, after, std::move(p));
    }

    void save() {
        if (recorder) recorder->save(root);
    }

}
