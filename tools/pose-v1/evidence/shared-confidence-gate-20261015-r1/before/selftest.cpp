#include "shared_output_gate.hpp"
#include <iostream>
#include <limits>
#include <stdexcept>

namespace gate = pose::shared_output_gate;
void need(bool condition, const char* label) {
    if (!condition) throw std::runtime_error(label);
}
int main() {
    gate::Scores a{}, b{};
    gate::Poses p{}, q{};
    need(gate::compare(a, b, p, q, 3.0).accepted, "identical values");
    p[4197] = 1.0f / 512.0f;
    auto r = gate::compare(a, b, p, q, 3.0);
    need(r.accepted && !r.poses_bitwise_equal && r.changed_pose_values == 1 &&
         r.max_joint_delta_mm == 1.953125, "last candidate/joint is checked and small drift accepted");
    p[4198] = 1.0f / 512.0f;
    p[4199] = 1.0f / 512.0f;
    r = gate::compare(a, b, p, q, 3.0);
    need(!r.accepted && r.max_coordinate_delta_mm < 3 && r.max_joint_delta_mm > 3,
         "three-dimensional norm must reject diagonal drift");
    p.fill(0); p[0] = 1.0f / 256.0f;
    need(!gate::compare(a, b, p, q, 3.0).accepted, "over-limit coordinate rejected");
    p.fill(0); p[0] = 1.0f / 512.0f;
    need(gate::compare(a, b, p, q, 1.953125).accepted, "inclusive exact limit");
    need(!gate::compare(a, b, p, q, std::nextafter(1.953125, 0.0)).accepted, "immediately below limit");
    a[99] = std::numeric_limits<float>::denorm_min();
    need(!gate::compare(a, b, p, q, 3.0).accepted, "even tiny score drift rejected");
    a.fill(0); a[0] = -0.0f;
    need(!gate::compare(a, b, p, q, 3.0).accepted, "signed-zero score identity retained");
    a.fill(0); p[0] = std::numeric_limits<float>::quiet_NaN();
    need(!gate::compare(a, b, p, q, 3.0).finite, "actual NaN rejected");
    p.fill(0); q[0] = std::numeric_limits<float>::infinity();
    need(!gate::compare(a, b, p, q, 3.0).finite, "reference infinity rejected");
    q.fill(0); b[0] = std::numeric_limits<float>::quiet_NaN();
    need(!gate::compare(a, b, p, q, 3.0).finite, "score NaN rejected");
    b.fill(0);
    need(!gate::compare(a, b, p, q, -1).accepted &&
         !gate::compare(a, b, p, q, std::numeric_limits<double>::infinity()).accepted, "invalid limits rejected");
    std::cout << "12 numerical gate boundary and rejection checks passed\n";
}
