#include "pcap_stream.hpp"
#include <algorithm>
#include <stdexcept>
#include <string>
#include <utility>

namespace nexmon_board {
namespace {
void require(bool condition, const char* message) {
	if (!condition)
		throw std::runtime_error(message);
}

std::uint16_t le16(const std::uint8_t* p) {
	return std::uint16_t(std::uint16_t(p[0]) | (std::uint16_t(p[1]) << 8));
}

std::uint32_t le32(const std::uint8_t* p) {
	return std::uint32_t(p[0]) | (std::uint32_t(p[1]) << 8) | (std::uint32_t(p[2]) << 16) |
		(std::uint32_t(p[3]) << 24);
}

std::uint16_t be16(const std::uint8_t* p) {
	return std::uint16_t((std::uint16_t(p[0]) << 8) | std::uint16_t(p[1]));
}

bool vlan(std::uint16_t type) {
	return type == 0x8100 || type == 0x88a8;
}

struct FrameError : std::runtime_error {
	using std::runtime_error::runtime_error;
};

void frame_require(bool condition, const char* message) {
	if (!condition)
		throw FrameError(message);
}
} // namespace

PcapStream::PcapStream(bool streaming, bool isolate) : streaming_(streaming), isolate_bad_frames_(isolate) {
	require(!isolate || streaming, "Bad-frame isolation requires explicit streaming mode");
	buffer_.reserve(max_buffer_);
}

bool PcapStream::complete() const noexcept {
	return !failed_ && header_read_ && buffer_.empty();
}

void PcapStream::finish() {
	require(!failed_, "PCAP parser already failed; restart an explicit acquisition");
	if (finished_)
		return;
	if (!complete()) {
		failed_ = true;
		throw std::runtime_error("Truncated PCAP global header or final record");
	}
	finished_ = true;
}

void PcapStream::parse_global_header() {
	const auto* p = buffer_.data();
	require(le32(p) == 0xa1b2c3d4, "Require little-endian microsecond classic PCAP");
	require(le16(p + 4) == 2 && le16(p + 6) == 4, "Require PCAP version 2.4");
	snaplen_ = le32(p + 16);
	require(snaplen_ >= 14 && snaplen_ <= max_frame_, "Invalid PCAP snaplen");
	require(le32(p + 20) == 1, "Require Ethernet PCAP link type 1");
	header_read_ = true;
	buffer_.clear();
	expected_ = 16;
}

void PcapStream::parse_record_header() {
	require(streaming_ || packets_ < max_packets_, "PCAP packet budget exceeds 40000");
	const auto* p = buffer_.data();
	const auto sec = le32(p), usec = le32(p + 4);
	const auto captured = le32(p + 8), original = le32(p + 12);
	require(usec < 1000000, "Invalid PCAP microsecond timestamp fraction");
	require(captured == original && captured >= 14 && captured <= snaplen_ && captured <= max_frame_,
		"Truncated or oversized PCAP Ethernet record");
	record_time_us_ = std::int64_t(sec) * 1000000 + usec;
	require(record_time_us_ >= last_time_us_, "PCAP receive time moves backwards");
	expected_ = 16 + std::size_t(captured);
	require(expected_ <= max_buffer_, "PCAP record buffer budget exceeded");
}

void PcapStream::parse_frame(std::vector<Datagram>& output) {
	const auto* frame = buffer_.data() + 16;
	const auto size = buffer_.size() - 16;
	std::size_t offset = 14;
	auto type = be16(frame + 12);
	for (unsigned layer = 0; layer < 2 && vlan(type); ++layer) {
		frame_require(size - offset >= 4, "Truncated Ethernet VLAN header");
		type = be16(frame + offset + 2);
		offset += 4;
	}
	frame_require(!vlan(type), "More than two Ethernet VLAN headers");
	if (type != 0x0800)
		return;
	frame_require(size - offset >= 20, "Truncated IPv4 header");
	const auto* ip = frame + offset;
	frame_require((ip[0] >> 4) == 4, "Invalid IPv4 version");
	const auto ihl = std::size_t(ip[0] & 15) * 4;
	const auto total = std::size_t(be16(ip + 2));
	frame_require(ihl >= 20 && ihl <= size - offset && total >= ihl && total <= size - offset,
		"Invalid IPv4 IHL/total length");
	frame_require((be16(ip + 6) & 0x3fff) == 0, "Fragmented IPv4 is not supported");
	if (ip[9] != 17)
		return;
	frame_require(total - ihl >= 8, "Truncated UDP header");
	const auto* udp = ip + ihl;
	const auto length = std::size_t(be16(udp + 4));
	frame_require(length >= 8 && length == total - ihl, "Invalid UDP length");
	const auto port = be16(udp + 2);
	if (port != 5500 && port != 5501)
		return;
	Datagram datagram;
	datagram.timestamp_us = record_time_us_;
	datagram.port = port;
	datagram.payload.assign(udp + 8, udp + length);
	output.push_back(std::move(datagram));
}

std::vector<Datagram> PcapStream::append(const std::uint8_t* data, std::size_t size) {
	require(!failed_, "PCAP parser already failed; restart an explicit acquisition");
	try {
		require(!finished_, "Cannot append after PCAP finish");
		require(data || size == 0, "Null PCAP chunk");
		require(
			streaming_ ? size <= 65536 : size <= max_bytes_ - bytes_, "PCAP chunk/job byte budget exceeded");
		bytes_ += size;
		std::vector<Datagram> output;
		std::size_t offset = 0;
		while (offset < size) {
			require(buffer_.size() < expected_ && expected_ <= max_buffer_,
				"Invalid or excessive incremental PCAP buffer");
			const auto take = std::min(expected_ - buffer_.size(), size - offset);
			buffer_.insert(buffer_.end(), data + offset, data + offset + take);
			offset += take;
			if (buffer_.size() != expected_)
				continue;
			if (!header_read_) {
				parse_global_header();
			} else if (expected_ == 16) {
				parse_record_header();
			} else {
				try {
					parse_frame(output);
				} catch (const FrameError& error) {
					if (!isolate_bad_frames_)
						throw;
					// The global/record headers and complete captured length
					// were already validated. Drop exactly this frame; never
					// scan for a guessed next boundary or publish its payload.
					++rejected_frames_;
					last_issue_.packet = packets_ + 1;
					last_issue_.timestamp_us = record_time_us_;
					last_issue_.reason = error.what();
					last_issue_.frame_prefix.assign(buffer_.begin() + 16,
						buffer_.begin() + 16 + std::min(std::size_t(64), buffer_.size() - 16));
				}
				++packets_;
				last_time_us_ = record_time_us_;
				buffer_.clear();
				expected_ = 16;
			}
		}
		return output;
	} catch (...) {
		failed_ = true;
		throw;
	}
}

} // namespace nexmon_board
