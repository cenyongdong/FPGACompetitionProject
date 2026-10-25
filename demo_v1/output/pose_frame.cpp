#include "pose_frame.hpp"
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <limits>

namespace pose::output {
    namespace {
        void need(bool value) { if (!value) throw std::runtime_error("Invalid PIWPOSE1 record"); }
        void put(Record& r, std::size_t off, std::uint64_t v, unsigned n) {
            for (unsigned i = 0; i < n; ++i) r[off + i] = static_cast<unsigned char>(v >> (8 * i));
        }
        std::uint64_t get(const Record& r, std::size_t off, unsigned n) {
            std::uint64_t v = 0;
            for (unsigned i = 0; i < n; ++i) v |= std::uint64_t(r[off + i]) << (8 * i);
            return v;
        }
        void put_float(Record& r, std::size_t off, float f) {
            std::uint32_t bits;
            std::memcpy(&bits, &f, 4);
            put(r, off, bits, 4);
        }
        float get_float(const Record& r, std::size_t off) {
            auto bits = static_cast<std::uint32_t>(get(r, off, 4));
            float f;
            std::memcpy(&f, &bits, 4);
            return f;
        }
        void validate(const Frame& f) {
            need(f.session != 0 && f.sequence != 0 && f.candidate < 100 && f.flags <= 1);
            need(std::isfinite(f.score));
            for (auto x : f.joints) need(std::isfinite(x));
        }
    }
    Record encode(const Frame& f) {
        validate(f);
        return encode_for_archive(f);
    }
    Record encode_for_archive(const Frame& f) {
        static_assert(sizeof(float) == 4 && std::numeric_limits<float>::is_iec559);
        Record r {};
        std::memcpy(r.data(), "PIWPOSE1", 8);
        put(r, 8, 1, 2); put(r, 10, 88, 2); put(r, 12, record_bytes, 4);
        put(r, 16, f.session, 8); put(r, 24, f.frame, 8); put(r, 32, f.invocation, 8);
        put(r, 40, f.source_ns, 8); put(r, 48, f.published_ns, 8);
        put(r, 56, f.candidate, 4); put(r, 60, 14, 2); put(r, 62, f.flags, 2);
        put_float(r, 64, f.score); put(r, 68, 1, 4); put(r, 72, 1, 4);
        put(r, 80, f.sequence, 8);
        for (std::size_t i = 0; i < 42; ++i) put_float(r, 88 + 4 * i, f.joints[i]);
        return r;
    }
    Frame decode(const Record& r) {
        need(std::memcmp(r.data(), "PIWPOSE1", 8) == 0);
        need(get(r, 8, 2) == 1 && get(r, 10, 2) == 88 && get(r, 12, 4) == record_bytes);
        need(get(r, 60, 2) == 14 && get(r, 68, 4) == 1 && get(r, 72, 4) == 1 && get(r, 76, 4) == 0);
        Frame f;
        f.session = get(r, 16, 8); f.frame = get(r, 24, 8); f.invocation = get(r, 32, 8);
        f.source_ns = get(r, 40, 8); f.published_ns = get(r, 48, 8);
        f.candidate = static_cast<std::uint32_t>(get(r, 56, 4));
        f.flags = static_cast<std::uint16_t>(get(r, 62, 2)); f.score = get_float(r, 64);
        f.sequence = get(r, 80, 8);
        for (std::size_t i = 0; i < 42; ++i) f.joints[i] = get_float(r, 88 + 4 * i);
        validate(f);
        return f;
    }
}
