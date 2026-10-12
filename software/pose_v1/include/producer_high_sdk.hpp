#pragma once
#include "producer_payload.hpp"
#include <memory>
#include "producer_phase_trace.hpp"
namespace pose::producer {
class SdkAddressGroup {
public:
    SdkAddressGroup(const std::filesystem::path& graph,const std::filesystem::path& raw,
             const std::filesystem::path& evidence,bool mock);
    ~SdkAddressGroup();
    SdkAddressGroup(const SdkAddressGroup&)=delete;
    SdkAddressGroup& operator=(const SdkAddressGroup&)=delete;
    void memoryRoundTrip(const Payload&,const std::filesystem::path&);
    void forwardSave(const Payload&,const std::filesystem::path&,size_t invocation,pose::producer_phase::Trace&,uint64_t planned);
private:struct Impl;std::unique_ptr<Impl> p_;
};
}
