#pragma once
#include <exception>

namespace pose180_pipeline {
// Call only inside an active catch handler; use the result before leaving it.
// No allocation and no assumption that an SDK exception derives from std.
inline const char* current_exception_message() noexcept {
	try {
		throw;
	} catch (const std::exception& error) {
		return error.what();
	} catch (...) {
		return "Non-standard exception";
	}
}
}
