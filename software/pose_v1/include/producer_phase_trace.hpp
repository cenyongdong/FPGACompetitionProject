#pragma once
#include <cstdint>
#include <filesystem>
#include <memory>
#include <utility>
namespace pose::producer_phase {
enum class Phase {Sleep,VideoCheck,Directory,SaveInput,SaveIdentity,SdkCall,Compare,
    SaveComparison,EndCheck,OwnerCheck,Validate,HostAllocate,HostStorage,
    InputBytes,HostWrite,JournalOpen,JournalFlush,Deadline,Reset,Forward,
    OutputStorage,Wait,OutputAllocate,Copy,HostRead,SaveOutput,SaveTrace};
class Trace {
public:
    explicit Trace(size_t capacity=16384);
    ~Trace();
    Trace(const Trace&)=delete;
    Trace& operator=(const Trace&)=delete;
    void invocation(unsigned);
    void mark(Phase,int64_t value,bool begin,bool exceptional=false);
    void check()const;
    void save(const std::filesystem::path&)const;
    class Span {
    public:
        Span(Trace&,Phase,int64_t);
        ~Span()noexcept;
        Span(const Span&)=delete;
    private:Trace& trace_;Phase phase_;int64_t value_;int exceptions_;
    };
    template<class F> decltype(auto) run(Phase phase,int64_t value,F&& f){
        Span span(*this,phase,value);return std::forward<F>(f)();
    }
private:struct Impl;std::unique_ptr<Impl> p_;
};
uint64_t now();
// Same absolute slot as the original schedule; never restart its clock.
bool beforeDeadline(uint64_t planned,uint64_t actual);
}
