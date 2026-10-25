#pragma once
#include "reference.hpp"

namespace pose::events::dataset {
    // Facts about the existing 2024 dataset, not a live sensor calibration.
    inline constexpr const char* profile = "person_in_wifi_3d_2024_audit_v1";
    inline constexpr unsigned joint_count = 14;
    inline constexpr const char* training_coordinate_unit = "m";
    inline constexpr bool training_preserves_npy_joint_order = true;
    inline constexpr unsigned paper_nominal_capture_fps = 15;
    // A paper's nominal rate does not recover per-sample capture timestamps.
    inline constexpr bool capture_timeline_verified = false;

    inline Config archived_config() {
        Config config;
        config.contract.mapping_evidence =
            "software/pose_events/dataset-contract-20261024.json: paper Table 2 is a candidate order; export map absent";
        config.contract.up_evidence =
            "software/pose_events/dataset-contract-20261024.json: display -C2 and label geometry are not physical calibration";
        // Neither a paper row order nor an observed upright skeleton authorizes these gates.
        config.contract.mapping_verified = false;
        config.contract.up_verified = false;
        return config;
    }
}
