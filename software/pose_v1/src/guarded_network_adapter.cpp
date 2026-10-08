// Link-time policy adapter for the isolated guarded integration target.
// The orchestration keeps the same owned-AU contract. Only this target links
// this adapter; the original online_rtsp.cpp implementation remains frozen.
#include "guarded_rtsp.hpp"

namespace pose::stream {
void serveOwnedAccessUnits(AccessUnitChannel& channel,
                          const RtspOptions& options,
                          const std::filesystem::path& evidence) {
    GuardedRtspOptions guarded;
    static_cast<RtspOptions&>(guarded) = options;
    serveGuardedAccessUnits(channel, guarded, evidence);
}
}
