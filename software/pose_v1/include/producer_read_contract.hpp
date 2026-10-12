#pragma once
#include <array>
#include <cstdint>
#include <exception>
#include <thread>
namespace pose::producer_read {
struct Source {uint64_t address,bytes,offset,capacity,chunk_identity;int64_t value;};
void validateSources(const std::array<Source,2>&);
class Guard {
public:
    uint64_t open();
    void check(uint64_t token)const;
    void idle()const;
    void close(uint64_t token);
    void expire();
    bool owner()const noexcept;
    uint64_t opened()const{return opened_;}
    uint64_t closed()const{return closed_;}
    uint64_t forced()const{return forced_;}
private:std::thread::id owner_=std::this_thread::get_id();bool alive_=true,active_=false;uint64_t token_=0,opened_=0,closed_=0,forced_=0;
};
// Both diagnostic and cleanup failures must preserve the original comparison error.
template<class D,class E,class C> void preserveFailure(std::exception_ptr original,D diagnostic,E saveError,C cleanup){
    try{diagnostic();}catch(...){try{saveError(std::current_exception());}catch(...){} }
    try{cleanup();}catch(...){try{saveError(std::current_exception());}catch(...){} }
    std::rethrow_exception(original);
}
}
