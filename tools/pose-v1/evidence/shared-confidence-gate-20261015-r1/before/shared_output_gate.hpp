#pragma once

#include <array>
#include <cmath>
#include <cstddef>
#include <cstring>

// Deployment comparison only. Does not change model outputs, rankings or SDK use.
namespace pose::shared_output_gate {
    using Scores = std::array<float, 100>;
    using Poses = std::array<float, 4200>;

    struct Result {
        bool finite = false;
        bool scores_bitwise_equal = false;
        bool poses_bitwise_equal = false;
        bool accepted = false;
        std::size_t changed_pose_values = 0;
        double max_coordinate_delta_mm = 0;
        double max_joint_delta_mm = 0;
    };

    inline Result compare(const Scores& actual_scores, const Scores& reference_scores,
                          const Poses& actual_poses, const Poses& reference_poses,
                          double max_allowed_joint_delta_mm) {
        Result r;
        if (!std::isfinite(max_allowed_joint_delta_mm) || max_allowed_joint_delta_mm <= 0) return r;
        for (std::size_t i = 0; i < actual_scores.size(); ++i) {
            if (!std::isfinite(actual_scores[i]) || !std::isfinite(reference_scores[i])) return r;
        }
        for (std::size_t i = 0; i < actual_poses.size(); ++i) {
            if (!std::isfinite(actual_poses[i]) || !std::isfinite(reference_poses[i])) return r;
        }
        r.finite = true;
        r.scores_bitwise_equal = std::memcmp(actual_scores.data(), reference_scores.data(), sizeof(Scores)) == 0;
        r.poses_bitwise_equal = std::memcmp(actual_poses.data(), reference_poses.data(), sizeof(Poses)) == 0;
        // Check every joint of all 100 candidates in the original slot order.
        // Use double for subtraction/norm; the gate must not add FP16 rounding.
        for (std::size_t i = 0; i < actual_poses.size(); i += 3) {
            double squared_mm = 0;
            for (std::size_t axis = 0; axis < 3; ++axis) {
                const auto index = i + axis;
                const double delta_mm = (double(actual_poses[index]) - double(reference_poses[index])) * 1000.0;
                squared_mm += delta_mm * delta_mm;
                if (std::abs(delta_mm) > r.max_coordinate_delta_mm) r.max_coordinate_delta_mm = std::abs(delta_mm);
                if (std::memcmp(&actual_poses[index], &reference_poses[index], sizeof(float)) != 0) ++r.changed_pose_values;
            }
            const double joint_mm = std::sqrt(squared_mm);
            if (joint_mm > r.max_joint_delta_mm) r.max_joint_delta_mm = joint_mm;
        }
        r.accepted = r.scores_bitwise_equal && r.max_joint_delta_mm <= max_allowed_joint_delta_mm;
        return r;
    }
}
