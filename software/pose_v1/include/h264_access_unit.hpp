#pragma once
#include <cstdint>
#include <optional>
#include <vector>

namespace pose::stream {
using Bytes=std::vector<uint8_t>;
struct AccessUnit {
    uint64_t id=0;
    int64_t ptsUs=0;
    Bytes sps,pps,slice; // Owned payloads, without Annex B prefixes.
    bool idr=false;
};
// The tested MVX contract: complete Annex B NALs per capture, one first_mb=0
// VCL slice per picture, stable SPS/PPS, no B-frame reordering. Not generic H264.
class AccessUnitAssembler {
public:
    std::optional<AccessUnit> consume(const Bytes&,int64_t ptsUs);
    uint64_t pictures() const {return count_;}
private:
    Bytes sps_,pps_;
    int64_t lastPts_=-1;
    uint64_t count_=0;
};
}
