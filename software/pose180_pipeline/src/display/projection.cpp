// Original public display projection relocated without arithmetic changes.
#include "skeleton_render.hpp"
#include <cmath>
#include <stdexcept>

namespace pose_v1::render {
namespace {
constexpr double pi = 3.14159265358979323846;

void need(bool ok, const char* why) {
	if (!ok)
		throw std::runtime_error(why);
}
}

std::array<double, 2> project(double a, double b, double c) {
	need(std::isfinite(a) && std::isfinite(b) && std::isfinite(c), "Non-finite coordinate");
	double x = a - 1.75, y = b - 1.75, z = -(c - 3.4);
	double cy = std::cos(pi / 6), sy = std::sin(pi / 6), ce = std::cos(pi / 9), se = std::sin(pi / 9);
	return {460 + 220 * (cy * x - sy * y), 355 - 220 * (ce * z - se * (sy * x + cy * y))};
}

}
