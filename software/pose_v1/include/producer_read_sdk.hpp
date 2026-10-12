#pragma once
#include "producer_payload.hpp"
#include <memory>
#include "producer_output_lease.hpp"
#include "producer_phase_trace.hpp"
namespace pose::producer {
class SdkReadGroup {
public:
    SdkReadGroup(const std::filesystem::path& graph,const std::filesystem::path& raw,
             const std::filesystem::path& evidence,bool mock);
    ~SdkReadGroup();
    SdkReadGroup(const SdkReadGroup&)=delete;
    SdkReadGroup& operator=(const SdkReadGroup&)=delete;
    void memoryRoundTrip(const Payload&,const std::filesystem::path&);
    std::unique_ptr<pose::producer_read::OutputLease> forwardSave(const Payload&,const std::filesystem::path&,size_t invocation,pose::producer_phase::Trace&,uint64_t planned);
private:struct Impl;std::unique_ptr<Impl> p_;
};
}
