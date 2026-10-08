#pragma once
#include "access_unit_channel.hpp"
#include <filesystem>

namespace pose::stream {
struct RtspOptions {unsigned port=8554,maximumSeconds=90,maximumClients=2;};
// Runs synchronously on one dedicated network thread. Caller owns the producer
// and must join it before destroying the channel. Fresh output directory only.
void serveOwnedAccessUnits(AccessUnitChannel&,const RtspOptions&,const std::filesystem::path& freshResults);
}
