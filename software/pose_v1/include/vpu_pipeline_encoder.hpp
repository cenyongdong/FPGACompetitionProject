#pragma once
#include "vpu_encoder.hpp"
#include <cstdint>
#include <functional>
#include <vector>

namespace pose::video {
constexpr std::size_t nv12FrameBytes=1280*720*3/2;
struct OwnedFrame {
    std::vector<uint8_t> nv12;
    uint64_t sourceFrame=0,invocation=0,generatedNs=0;
    unsigned encodedId=0;
    bool repeatedSource=false;
    bool inferenceResult=true; // false only for explicitly labelled startup NoInput
};
struct OwnedPacket {
    std::vector<uint8_t> bytes;
    int64_t ptsUs=0;
    unsigned flags=0,sequence=0;
};
using FrameProducer=std::function<OwnedFrame(unsigned)>;
using PacketConsumer=std::function<void(OwnedPacket)>;
// Pure Host check, also performed before copying/queuing each produced frame.
void validateOwnedFrame(const OwnedFrame&,unsigned requestedId);
// Finite serial diagnostic. Nominal10fps PTS; not a realtime pacing contract.
// Every capture is copied into owned bytes before callback/driver requeue.
EncodeResult encodeNv12Producer(const std::filesystem::path& newOutputDirectory,
                               const EncodeOptions&,FrameProducer,PacketConsumer,
                               unsigned primeInputs=6);
}
