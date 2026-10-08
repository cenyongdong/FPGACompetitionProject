#pragma once
#include "pipeline_fixture_source.hpp"

namespace pose::validation {
// Diagnostic adapter only: preserve the first rejected result, then rethrow.
// Successful oracle checks and the production Engine remain unchanged.
void saveOrCaptureFailedResult(const FixtureWindow&,const pose_v1::application::Result&,
                               const pose_v1::Window&,size_t,const std::filesystem::path&,
                               std::ofstream&);
}
