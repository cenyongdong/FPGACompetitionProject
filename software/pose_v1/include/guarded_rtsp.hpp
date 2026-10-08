#pragma once
#include "online_rtsp.hpp"

namespace pose::stream {
struct GuardedRtspOptions:RtspOptions {
    unsigned sendBufferBytes=65536; // Per TCP client, no system-wide tuning.
};
// Isolated candidate: actual socket buffer bounds and RTP error propagation.
void serveGuardedAccessUnits(AccessUnitChannel&,const GuardedRtspOptions&,const std::filesystem::path&);
}
