#include "shared_output_gate.hpp"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

template<class T> T read(const std::string& path) {
    std::ifstream in(path, std::ios::binary);
    T value{};
    if (!in.read(reinterpret_cast<char*>(value.data()), sizeof(T)) ||
        in.peek() != std::char_traits<char>::eof()) throw std::runtime_error("Invalid array file: " + path);
    return value;
}
int main(int argc, char** argv) {
    if (argc != 5) throw std::runtime_error("actual-scores reference-scores actual-poses reference-poses required");
    namespace gate = pose::shared_output_gate;
    const auto result = gate::compare(read<gate::Scores>(argv[1]), read<gate::Scores>(argv[2]),
                                      read<gate::Poses>(argv[3]), read<gate::Poses>(argv[4]), 3.0, 0.2f);
    std::cout << std::setprecision(17) << std::boolalpha
        << "{\"accepted\":" << result.accepted << ",\"finite\":" << result.finite
        << ",\"scores_bitwise_equal\":" << result.scores_bitwise_equal
        << ",\"poses_bitwise_equal\":" << result.poses_bitwise_equal
        << ",\"checked_candidates\":" << result.checked_candidates
        << ",\"excluded_candidates\":" << result.excluded_candidates
        << ",\"max_joint_delta_mm\":" << result.max_joint_delta_mm
        << ",\"max_checked_joint_delta_mm\":" << result.max_checked_joint_delta_mm
        << ",\"max_excluded_joint_delta_mm\":" << result.max_excluded_joint_delta_mm
        << ",\"excluded_over_limit_joints\":" << result.excluded_over_limit_joints << "}\n";
    return result.accepted ? 0 : 1;
}
