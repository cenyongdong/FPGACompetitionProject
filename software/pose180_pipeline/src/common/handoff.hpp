#pragma once
#include <chrono>
#include <condition_variable>
#include <cstdint>
#include <exception>
#include <mutex>
#include <stdexcept>

namespace pose180_pipeline {
// Publisher keeps the pool lease alive until the SDK owner proves adoption.
// No result copy and no SDK access from this thread.
template <class T> class Handoff {
	std::mutex mutex_;
	std::condition_variable cv_;
	const T* slot_ = nullptr;
	bool done_ = false;
	std::exception_ptr error_;

	template <class P> void wait(std::unique_lock<std::mutex>& lock, P predicate) {
		if (!cv_.wait_for(lock, std::chrono::seconds(5), [&] {
				return error_ || predicate();
			}))
			throw std::runtime_error("Archive/display handoff deadline");
		if (error_)
			std::rethrow_exception(error_);
	}

public:
	void fail(std::exception_ptr e) {
		std::lock_guard<std::mutex> lock(mutex_);
		if (!error_)
			error_ = e;
		cv_.notify_all();
	}

	void submit(const T& value) {
		std::unique_lock<std::mutex> lock(mutex_);
		if (slot_)
			throw std::logic_error("Occupied display handoff");
		if (error_)
			std::rethrow_exception(error_);
		slot_ = &value;
		done_ = false;
		cv_.notify_all();
		wait(lock, [&] {
			return done_;
		});
		slot_ = nullptr;
		cv_.notify_all();
	}

	const T& take() {
		std::unique_lock<std::mutex> lock(mutex_);
		wait(lock, [&] {
			return slot_ && !done_;
		});
		return *slot_;
	}

	void complete(std::uint64_t invocation) {
		std::lock_guard<std::mutex> lock(mutex_);
		if (!slot_ || slot_->invocation != invocation || done_)
			throw std::logic_error("Display handoff identity differs");
		done_ = true;
		cv_.notify_all();
	}
};
}
