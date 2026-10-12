#pragma once
#include <icraft-xrt/core/device.h>
#include "producer_address_contract.hpp"
#include <filesystem>
#include <memory>
namespace pose::producer_address {
class Reservation {
public:
    Reservation(const icraft::xrt::Device&,const std::filesystem::path&);
    ~Reservation();
    Reservation(const Reservation&)=delete;
    void recordAllocated(const std::filesystem::path&)const;
    void checkBoundary(uint64_t address,uint64_t bytes,uint64_t identity)const;
    void release(const std::filesystem::path&);
private:struct Impl;std::unique_ptr<Impl> p_;
};
}
