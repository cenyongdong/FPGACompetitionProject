#pragma once
#include <array>
#include <cstdint>

// SDK无关的拥有值；坐标保持模型C0/C1/C2原值，不携带设备地址。
namespace pose::output {
    constexpr std::size_t record_bytes = 256;
    struct Frame {
        std::uint64_t session = 0, frame = 0, invocation = 0;
        std::uint64_t source_ns = 0, published_ns = 0, sequence = 0;
        std::uint32_t candidate = 0;
        std::uint16_t flags = 1; // bit0: archived real board output
        float score = 0;
        std::array<float, 42> joints {};
    };
    using Record = std::array<unsigned char, record_bytes>;
    Record encode(const Frame&);
    // 完整原值归档专用；调用方必须先持久保存，再validate并确认可发布。
    Record encode_for_archive(const Frame&);
    Frame decode(const Record&);
}
