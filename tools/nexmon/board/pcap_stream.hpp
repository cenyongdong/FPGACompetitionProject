#pragma once
#include <cstddef>
#include <cstdint>
#include <vector>

namespace nexmon_board {

struct Datagram {
    std::int64_t timestamp_us = 0;
    std::uint16_t port = 0;
    std::vector<std::uint8_t> payload;
};

// Incremental parser for capture-metadata's little-endian microsecond classic
// Ethernet PCAP stdout. Feed arbitrary chunks in their original stream order.
// The caller preserves raw input before append; this parser does no file I/O.
class PcapStream {
public:
    explicit PcapStream(bool streaming=false);
    std::vector<Datagram> append(const std::uint8_t* bytes,std::size_t size);
    // True only after a valid global header and at a whole-record boundary.
    bool complete() const noexcept;
    // Rejects truncated headers/frames, then permanently closes input.
    void finish();
    // Counts all PCAP records/raw stream bytes, including unselected protocols.
    std::size_t packets() const noexcept { return packets_; }
    std::size_t bytes() const noexcept { return bytes_; }

private:
    static constexpr std::size_t max_packets_ = 40000;
    static constexpr std::size_t max_bytes_ = 32u*1024u*1024u;
    static constexpr std::size_t max_frame_ = 65535;
    static constexpr std::size_t max_buffer_ = 16+max_frame_;
    std::vector<std::uint8_t> buffer_;
    std::size_t expected_ = 24,packets_ = 0,bytes_ = 0;
    std::uint32_t snaplen_ = 0;
    std::int64_t record_time_us_ = 0,last_time_us_ = -1;
    bool header_read_ = false,finished_ = false,failed_ = false;
    bool streaming_ = false;
    void parse_global_header();
    void parse_record_header();
    void parse_frame(std::vector<Datagram>& output);
};

} // namespace nexmon_board
