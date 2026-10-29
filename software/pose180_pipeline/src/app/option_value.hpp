#pragma once
#include <charconv>
#include <cmath>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <string>

namespace pose180_demo {
// Parse the entire value before conversion/narrowing. std::stoul alone accepts
// negative signs and trailing text; multiplying such a duration can wrap.
inline std::uint64_t unsigned_option(
	const std::string& value, const char* name, std::uint64_t maximum = UINT64_MAX) {
	std::uint64_t result = 0;
	const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
	if (parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size() || result > maximum)
		throw std::invalid_argument(std::string("Invalid unsigned option ") + name);
	return result;
}

inline double real_option(const std::string& value, const char* name) {
	std::size_t consumed = 0;
	const double result = std::stod(value, &consumed);
	if (consumed != value.size() || !std::isfinite(result))
		throw std::invalid_argument(std::string("Invalid finite option ") + name);
	return result;
}
} // namespace pose180_demo
