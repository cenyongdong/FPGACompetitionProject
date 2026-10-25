// Model-specific runtime contract. Filled only after complete SDK fusion validation.
#pragma once
#include <map>
#include <set>
#include <vector>
#include <utility>
#include <cstdint>
namespace pose_v1::fusion_baseline {
    inline const std::set<int64_t> host_ids = {0,188,192,437,442,565};
    inline std::map<int64_t,std::vector<int64_t>> members;
    inline std::map<int64_t,std::pair<int,int>> sync;
    inline uint32_t final_count = 0;
}
