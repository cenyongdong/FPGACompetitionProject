#include "dataset.hpp"
#include "exception_message.hpp"
#include <fstream>
#include <stdexcept>

namespace pose180_demo {
Dataset::Dataset(
	Shared& shared, const std::filesystem::path& file, std::uint64_t session, unsigned repetitions)
	: shared_(shared) {
	const auto bytes = std::filesystem::file_size(file);
	if (!bytes || bytes % pp::input_bytes || bytes / pp::input_bytes > 9000)
		throw std::runtime_error("Dataset must contain 1..9000 complete PIWCSI2 records");
	if (!repetitions || repetitions > 30 || bytes / pp::input_bytes * repetitions > 9000 ||
		session > UINT64_MAX - repetitions)
		throw std::runtime_error("Dataset repetitions require 1..30 passes and at most 9000 total inputs");

	// 文件大小、播放次数先验证完成，再创建持有文件流的输入线程。
	auto input = std::ifstream(file, std::ios::binary);
	if (!input)
		throw std::runtime_error("Cannot open dataset input");
	thread_ = std::thread([&, session, bytes, repetitions, input = std::move(input)]() mutable {
		try {
			auto wait = [&](std::uint64_t until) {
				while (!shared.stop && !shared.stats.isolated && now_ns() < until)
					std::this_thread::sleep_for(std::chrono::milliseconds(1));
				return !shared.stop && !shared.stats.isolated;
			};

			while (!shared.stop && !shared.stats.isolated && !shared.stats.initialized)
				std::this_thread::sleep_for(std::chrono::milliseconds(5));
			if (shared.stop || shared.stats.isolated)
				return;
			shared.stats.input_connected = true;
			std::array<unsigned char, pp::input_bytes> record{};
			for (unsigned pass = 0; pass < repetitions; ++pass) {
				if (shared.stop || shared.stats.isolated)
					return;
				input.clear();
				input.seekg(0);

				// 每次重播使用新 epoch，保留原帧号和时间戳，避免首尾误接为连续动作。
				shared.stats.input_epoch = session + pass;
				shared.input.clear();
				std::uint64_t previous_time = 0, previous_frame = 0, deadline = now_ns();
				for (std::uint64_t i = 0; i < bytes / pp::input_bytes; ++i) {
					if (!input.read(reinterpret_cast<char*>(record.data()), record.size()))
						throw std::runtime_error("Dataset input truncated while reading");
					Input value;
					pp::decode_input(record, value.window);
					const auto stamp = value.window.source_time_ns;
					if (!stamp || value.window.frame_id <= previous_frame ||
						(i && (stamp <= previous_time || stamp - previous_time > 1000000000ull)))
						throw std::runtime_error("Dataset order or pacing interval invalid");

					if (i)
						deadline += stamp - previous_time;
					if (!wait(deadline)) {
						shared.stats.input_connected = false;
						return;
					}

					// 从实际送入时间安排下一帧，磁盘迟读后不突发补发积压帧。
					deadline = now_ns();
					value.arrived = deadline;
					value.epoch = session + pass;
					accept_input(shared, value);
					previous_time = stamp;
					previous_frame = value.window.frame_id;
				}

				++shared.stats.dataset_passes;
				// Leave the last input its normal processing window before the
				// next epoch. Late inference is isolated by the existing epoch test.
				if (pass + 1 < repetitions && !wait(deadline + 100000000ull)) {
					shared.stats.input_connected = false;
					return;
				}
			}

			// EOF 交给主循环收尾，最后一个待消费窗口仍可正常处理。
			shared.stats.input_connected = false;
			shared.stats.dataset_done = true;
		} catch (...) {
			++shared.stats.malformed;
			shared.stats.input_connected = false;
			shared.stats.isolated = true;
			try {
				shared.stats.input_error(pose180_pipeline::current_exception_message());
			} catch (...) {
			}
		}
	});
}

Dataset::~Dataset() {
	shared_.stop = true;
	if (thread_.joinable())
		thread_.join();
}
}
