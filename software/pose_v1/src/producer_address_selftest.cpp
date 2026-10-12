#include "producer_address_contract.hpp"
#include <iostream>
#include <stdexcept>
namespace {void need(bool x){if(!x){throw std::runtime_error("Address test failed");}}template<class F>void reject(F f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}need(caught);}}
int main(){try{
    namespace a=pose::producer_address;a::Pool p{4096,4294963200ULL};a::Block prefix{4096,a::prefixBytes,1},data{a::prefixBytes+61440,30240,2},index{a::prefixBytes+40960,16800,3};
    a::validatePool(p,{});a::validatePrefix(p,prefix);a::validateMap(p,prefix,{prefix,data,index});a::validateBoundary(data);a::validateBoundary(index);
    reject([&]{a::validatePool(p,{prefix});});reject([&]{a::validatePool({4096,UINT64_MAX},{});});
    reject([&]{auto b=prefix;b.bytes--;a::validatePrefix(p,b);});reject([&]{auto b=prefix;b.start++;a::validatePrefix(p,b);});
    reject([&]{auto b=data;b.identity=0;a::validateBoundary(b);});reject([&]{auto b=data;b.start=UINT64_MAX-5;a::validateBoundary(b);});
    reject([&]{auto b=data;b.start=a::lower-64;a::validateBoundary(b);});reject([&]{auto b=data;b.start=a::upper-64;a::validateBoundary(b);});
    reject([&]{auto b=data;b.start++;a::validateBoundary(b);});reject([&]{a::validateMap(p,prefix,{data,index});});
    reject([&]{auto b=data;b.identity=index.identity;a::validateMap(p,prefix,{prefix,b,index});});
    reject([&]{auto b=data;b.start=index.start;a::validateMap(p,prefix,{prefix,b,index});});
    std::cout<<"Managed prefix/band/range/overflow/ownership12 rejection contracts passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
