#pragma once
#include <atomic>
#include <chrono>
#include <cstdint>
#include <fcntl.h>
#include <sstream>
#include <stdexcept>
#include <sys/mman.h>
#include <sys/stat.h>
#include <thread>
#include <unistd.h>

namespace pose180_demo::startup_consumer {
inline void need(bool value, const char* message) {
	if (!value)
		throw std::runtime_error(message);
}

struct Snapshot {
	std::uint32_t control, request, response, status, flags;
};

inline bool released_idle(const Snapshot& s) {
	return (s.flags & 0x7e) == 0x0c && !(s.control & 3) && s.request == s.response;
}

inline bool healthy(const Snapshot& s) {
	return released_idle(s) && s.status == 0 && !(s.flags & 0x10081) && !(s.control & 4);
}

inline bool consumed(const Snapshot& s) {
	const auto beats = (s.status >> 3) & 511;
	return released_idle(s) && (s.status & 7) == 2 && beats > 0 && beats < 256 && (s.status & (1u << 25)) &&
		!(s.status & 0x8c000000u) && (s.flags & 0x10081) == 1 && (s.control & 4);
}

class Control {
	int fd_ = -1;
	void* page_ = MAP_FAILED;
	volatile std::uint32_t* csr_ = nullptr;

public:
	Control() {
		fd_ = ::open("/dev/mem", O_RDWR | O_SYNC | O_CLOEXEC);
		need(fd_ >= 0, "Cannot open startup-consumer CSR device");
		struct stat info{};
		if (::fstat(fd_, &info) != 0 || !S_ISCHR(info.st_mode)) {
			::close(fd_);
			fd_ = -1;
			throw std::runtime_error("Expected physical CSR device");
		}
		page_ = ::mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_SHARED, fd_, 0x400b0000);
		if (page_ == MAP_FAILED) {
			::close(fd_);
			fd_ = -1;
			throw std::runtime_error("Cannot map startup-consumer CSR");
		}
		csr_ = reinterpret_cast<volatile std::uint32_t*>(static_cast<char*>(page_) + 0x800);
	}

	~Control() {
		if (page_ != MAP_FAILED)
			::munmap(page_, 4096);
		if (fd_ >= 0)
			::close(fd_);
	}

	Control(const Control&) = delete;
	Control& operator=(const Control&) = delete;

	std::uint32_t read(unsigned offset) const {
		need(offset <= 0x14 && !(offset & 3), "Invalid startup CSR read");
		auto value = csr_[offset / 4];
		std::atomic_thread_fence(std::memory_order_seq_cst);
		return value;
	}

	void command(std::uint32_t value) {
		need(value == 0x534e4150 || value == 0x434f4e53, "Invalid startup consumer command");
		need(read(4) == 0x48444302, "Wrong functional startup-consumer ABI");
		need(!(read(0) & 3), "Startup consumer CSR busy/error");
		const auto sequence = read(8) + 1;
		std::atomic_thread_fence(std::memory_order_seq_cst);
		csr_[0] = value; // One native volatile 32-bit MMIO write, never a memory clear.
		std::atomic_thread_fence(std::memory_order_seq_cst);
		const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(100);
		while (true) {
			const auto status = read(0);
			need(!(status & 2), "Startup consumer rejected command");
			if (!(status & 1) && read(8) == sequence && read(12) == sequence)
				return;
			need(std::chrono::steady_clock::now() < deadline, "Startup consumer acknowledgement timeout");
			std::this_thread::sleep_for(std::chrono::microseconds(100));
		}
	}

	Snapshot snapshot() {
		command(0x534e4150);
		return {read(0), read(8), read(12), read(16), read(20)};
	}
};

template <class Emit> void prepare(Emit emit) {
	Control control;
	auto sample = [&](const char* stage) {
		const auto s = control.snapshot();
		std::ostringstream row;
		row << "{\"startup_consumer\":\"" << stage << "\",\"control\":" << s.control
			<< ",\"request\":" << s.request << ",\"response\":" << s.response << ",\"status\":" << s.status
			<< ",\"flags\":" << s.flags << "}\n";
		emit(row.str());
		return s;
	};
	need(control.read(4) == 0x48444302, "Wrong startup-consumer bitstream");
	need(control.read(8) == 0 && control.read(12) == 0 && control.read(0) == 0,
		"Startup consumer already used in this configuration");
	auto before = sample("before");
	// Allow an already-present PS return to reach the S01 buffer before deciding.
	for (unsigned i = 0; i < 10 && (before.flags & 0x10000) && !(before.flags & 0x80); ++i) {
		need(released_idle(before) && before.status == 0, "Return path is not idle before consumption");
		std::this_thread::sleep_for(std::chrono::milliseconds(20));
		before = sample("settle");
	}
	bool used = false;
	if (!healthy(before)) {
		need(released_idle(before) && before.status == 0 && !(before.flags & 1) && !(before.control & 4) &&
				(before.flags & 0x7f80) == 0x80,
			"Return does not satisfy bounded startup consumption conditions");
		control.command(0x434f4e53);
		used = true;
		const auto deadline = std::chrono::steady_clock::now() + std::chrono::milliseconds(100);
		auto after = sample("consume");
		while ((after.status & 7) == 1 && std::chrono::steady_clock::now() < deadline) {
			std::this_thread::sleep_for(std::chrono::milliseconds(1));
			after = sample("consume");
		}
		need(consumed(after), "Startup consumption did not finish safely");
	}
	std::this_thread::sleep_for(std::chrono::milliseconds(20));
	const auto final = sample("before_SDK");
	need(used ? consumed(final) : healthy(final), "Startup return path changed before SDK");
	emit(used ? "startup_mode=consumed; protocol_checker_present=0\n"
			  : "startup_mode=healthy; protocol_checker_present=0\n");
}
}
