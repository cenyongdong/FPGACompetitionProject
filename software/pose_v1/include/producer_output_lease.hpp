#pragma once
#include <filesystem>
#include <cstdint>
#include <memory>
namespace pose::producer_read {
struct ReadScope;
class OutputLease {
public:
    ~OutputLease();
    OutputLease(const OutputLease&)=delete;
    void close();
    void captureFailure(const std::filesystem::path&);
    OutputLease(std::shared_ptr<ReadScope>,uint64_t token);
private:std::shared_ptr<ReadScope> scope_;uint64_t token_;bool closed_=false;
};
}
