#pragma once
#include <array>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <chrono>
#include <functional>

namespace pose::post {
// Compact status is NOT a substitute for unknown/missing native rule coverage.
struct LeanReceipt {
	std::uint32_t abi = 0, state = 0, faults = 0, request = 0, response = 0;
	bool native_dependency_present = false, coverage_complete = false;
	std::array<std::uint32_t, 5> native_history{};
};

inline bool lean_admitted(const LeanReceipt& r, const std::string& profile) {
	constexpr std::array<std::uint32_t, 5> allowed{0, 0x2c000000, 0xb0000000, 0, 0};
	for (unsigned i = 0; i < 5; ++i)
		if (r.native_history[i] & ~allowed[i])
			return false;
	return profile == "pose-stabilizer-offline-v1" && r.abi == 0x4c534701 && r.state == 4 && r.faults == 0 &&
		r.request != 0 && r.request == r.response && r.coverage_complete && r.native_dependency_present;
}

inline void require_lean_deployment_qualification(bool qualified) {
	if (!qualified)
		throw std::runtime_error("Lean startup is an offline candidate; no deployment qualification");
}

struct LeanSnapshot {
	LeanReceipt receipt;
	std::array<std::uint32_t, 32> words{};
};

class LeanGuard {
	std::function<std::uint32_t(unsigned)> read_;
	std::function<void(unsigned, std::uint32_t)> write_;

public:
	// Access callbacks must be supplied by the single device owner after independent
	// hardware/BOOT identity validation. This is not an MMIO mapping implementation.
	LeanGuard(const std::string& profile, decltype(read_) read, decltype(write_) write)
		: read_(read), write_(write) {
		if (profile != "pose-stabilizer-offline-v1")
			throw std::runtime_error("Lean guard profile mismatch");
		if (read_(4) != 0x4c534701)
			throw std::runtime_error("Lean guard ABI mismatch");
	}

	// 0 snapshot, 1 one-shot arm, 2 checker rearm, 3 admission request.
	// Caller may issue 1..3 only before SDK/DMA/HDMI activity. No automatic retry.
	LeanSnapshot request(unsigned opcode) {
		if (opcode > 3 || read_(0) != 0)
			throw std::runtime_error("Lean command invalid/busy/faulted");
		const auto before = read_(8);
		if (before == UINT32_MAX)
			throw std::runtime_error("Lean sequence exhausted");
		write_(0, opcode);
		const auto expected = before + 1;
		const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(10);
		while (read_(12) != expected) {
			if ((read_(0) & 2) || std::chrono::steady_clock::now() >= deadline)
				throw std::runtime_error("Lean command unacknowledged; no retry");
		}
		LeanSnapshot s;
		s.receipt.abi = read_(4);
		s.receipt.request = read_(8);
		s.receipt.response = read_(12);
		for (unsigned i = 0; i < 32; ++i)
			s.words[i] = read_(0x40 + 4 * i);
		if (read_(0) != 0 || read_(8) != expected || read_(12) != expected || s.receipt.request != expected ||
			s.receipt.response != expected)
			throw std::runtime_error("Lean snapshot changed/invalid");
		s.receipt.state = s.words[0];
		s.receipt.faults = s.words[1];
		s.receipt.coverage_complete = s.words[27] == 1;
		s.receipt.native_dependency_present = s.words[28] == 1;
		for (unsigned i = 0; i < 5; ++i)
			s.receipt.native_history[i] = s.words[17 + i];
		return s;
	}
};
}
