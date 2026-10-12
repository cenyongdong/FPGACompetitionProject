#include "plddr_position_contract.hpp"
#include <functional>
#include <iostream>
#include <stdexcept>
#include <limits>
int main(){try{
    namespace p=pose::plddr_position;
    p::Pool pool{4096,4294963200};p::Block prefix{4096,p::prefixBytes,1},a{4096+p::prefixBytes,30240,2},padding{4096+p::prefixBytes+30240,32,3},b{4096+p::prefixBytes+30272,16800,4};
    p::validatePool(pool,{});p::validateAllocated(pool,prefix,a,padding,b);
    unsigned refused=0;auto reject=[&](const std::function<void()>&f){bool failed=false;try{f();}catch(const std::exception&){failed=true;}if(!failed){throw std::runtime_error("Invalid position accepted");}++refused;};
    reject([&]{p::validatePool({0,0},{});});reject([&]{p::validatePool({UINT64_MAX-1,4},{});});
    reject([&]{p::validatePool(pool,{a});});reject([&]{p::validatePool({4096,32*1024*1024},{});});
    reject([&]{auto c=prefix;c.bytes--;p::validateAllocated(pool,c,a,padding,b);});
    reject([&]{auto c=a;c.identity=0;p::validateAllocated(pool,prefix,c,padding,b);});
    reject([&]{auto c=b;c.identity=a.identity;p::validateAllocated(pool,prefix,a,padding,c);});
    reject([&]{auto c=b;c.start=a.start;p::validateAllocated(pool,prefix,a,padding,c);});
    reject([&]{auto c=a;c.start=p::sourceLower-64;p::validateAllocated(pool,prefix,c,padding,b);});
    reject([&]{auto c=b;c.start=p::sourceUpper-64;p::validateAllocated(pool,prefix,a,padding,c);});
    reject([&]{auto c=b;c.start++;p::validateAllocated(pool,prefix,a,padding,c);});
    reject([&]{auto c=b;c.bytes=UINT64_MAX;p::validateAllocated(pool,prefix,a,padding,c);});
    if(refused!=12){throw std::runtime_error("Refusal count differs");}
    std::cout<<"{\"status\":\"passed\",\"refusals\":12,\"legal_position\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
