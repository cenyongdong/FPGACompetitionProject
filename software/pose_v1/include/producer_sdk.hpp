#pragma once
#include "producer_payload.hpp"
#include <memory>
namespace pose::producer {
class SdkGroup {
public:
    SdkGroup(const std::filesystem::path& graph,const std::filesystem::path& raw,
             const std::filesystem::path& evidence,bool mock);
    ~SdkGroup();
    SdkGroup(const SdkGroup&)=delete;
    SdkGroup& operator=(const SdkGroup&)=delete;
    void memoryRoundTrip(const Payload&,const std::filesystem::path&);
    void forwardSave(const Payload&,const std::filesystem::path&,size_t invocation);
private:struct Impl;std::unique_ptr<Impl> p_;
};
}
