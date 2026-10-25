#pragma once
#include <cstdint>

namespace pose_v1::application {
struct Result {
    uint64_t invocation = 0;
    uint64_t frame_id = 0;
};
}
