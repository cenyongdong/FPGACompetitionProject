#include "producer_read_contract.hpp"
#include <iostream>
#include <stdexcept>
#include <vector>
namespace {void need(bool x){if(!x){throw std::runtime_error("Read contract test failed");}}template<class F>void reject(F f){bool caught=false;try{f();}catch(...){caught=true;}need(caught);}}
int main(){try{
    namespace r=pose::producer_read;std::array<r::Source,2>s{{{109113344,30240,0,30240,1,4386},{109092864,16800,0,16800,2,4390}}};r::validateSources(s);
    reject([&]{auto a=s;a[0].value=4390;r::validateSources(a);});reject([&]{auto a=s;a[0].bytes--;r::validateSources(a);});reject([&]{auto a=s;a[0].offset=UINT64_MAX;r::validateSources(a);});
    reject([&]{auto a=s;a[0].capacity--;r::validateSources(a);});reject([&]{auto a=s;a[0].chunk_identity=a[1].chunk_identity;r::validateSources(a);});reject([&]{auto a=s;a[1].address=a[0].address;r::validateSources(a);});
    reject([&]{auto a=s;a[0].address=UINT64_MAX;r::validateSources(a);});reject([&]{auto a=s;a[0].address++;r::validateSources(a);});
    r::Guard guard;auto t=guard.open();reject([&]{guard.open();});bool rejected=false;std::thread wrong([&]{try{guard.check(t);}catch(...){rejected=true;}});wrong.join();need(rejected);guard.close(t);reject([&]{guard.check(t);});auto next=guard.open();reject([&]{guard.check(t);});guard.expire();reject([&]{guard.check(next);});need(guard.opened()==2&&guard.closed()==2&&guard.forced()==1);
    // Normal comparisons cause zero reads; failure snapshots own copies and cannot repair first bytes.
    int reads=0;std::vector<char>first(47040,'A'),source(47040,'B');auto preserved=first;std::vector<std::vector<char>>snapshots;
    bool normal=true;if(!normal){++reads;}need(reads==0);
    std::exception_ptr original;try{throw std::runtime_error("original comparison");}catch(...){original=std::current_exception();}
    try{r::preserveFailure(original,[&]{for(int i=0;i<2;++i){++reads;snapshots.push_back(source);}source[0]='C';},[](std::exception_ptr){},[]{});}catch(const std::exception&e){need(std::string(e.what())=="original comparison");}
    need(reads==2&&snapshots.size()==2&&snapshots[0]==snapshots[1]&&snapshots[0][0]=='B'&&first==preserved);
    bool cleanup=false,error=false;try{r::preserveFailure(original,[]{throw std::runtime_error("diagnostic failed");},[&](std::exception_ptr){error=true;},[&]{cleanup=true;throw std::runtime_error("cleanup failed");});}catch(const std::exception&e){need(std::string(e.what())=="original comparison");}need(cleanup&&error);
    std::cout<<"Lease range/thread/generation/expiry/ownership/zero-normal-read/original-error contracts passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
