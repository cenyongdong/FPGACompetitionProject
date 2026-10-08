#pragma once
#include "vpu_pipeline_encoder.hpp"
#include <optional>

namespace pose::video {
struct ResidentOptions {
    bool allowVpuStream=false;
    unsigned frameLimit=1000;
};
// Called only on the encoding thread. nullopt requests normal drain.
// Implementations must return promptly; inference runs on its own thread.
struct ResidentSample {OwnedFrame frame;uint64_t sampledNs=0;};
using ResidentProducer=std::function<std::optional<ResidentSample>(unsigned,uint64_t)>;
// Invoked once after an actual nonempty capture; wakes the inference thread.
EncodeResult encodeResident(const std::filesystem::path& newOutputDirectory,
    const ResidentOptions&,ResidentProducer,PacketConsumer,std::function<void()> onFirstCapture);
}
