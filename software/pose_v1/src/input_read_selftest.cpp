#include "input_read_contract.hpp"
#include <array>
#include <algorithm>
#include <iostream>
#include <stdexcept>
#include <cstring>
int main(){try{
    using namespace pose::input_read;std::array<char,64> owned{};owned.fill(77);size_t reads=0,refused=0;
    auto reader=[&](char*p,size_t n){++reads;std::memset(p,31,n);};
    boundedRead({owned.data()+8,8,64},48,reader);
    if(reads!=1||!std::all_of(owned.begin(),owned.begin()+8,[](char v){return v==77;})||
       !std::all_of(owned.begin()+8,owned.begin()+56,[](char v){return v==31;})||
       !std::all_of(owned.begin()+56,owned.end(),[](char v){return v==77;}))throw std::runtime_error("Guard/ownership mismatch");
    const auto reject=[&](HostView v,size_t n,const std::function<void(char*,size_t)>& f){bool caught=false;try{boundedRead(v,n,f);}catch(const std::exception&){caught=true;++refused;}if(!caught)throw std::runtime_error("Invalid read accepted");};
    reject({nullptr,0,64},4,reader);reject({owned.data(),0,64},0,reader);
    reject({owned.data(),65,64},4,reader);reject({owned.data(),64,64},4,reader);
    reject({owned.data(),8,64},57,reader);reject({owned.data(),0,64},65,reader);
    reject({owned.data(),0,2*1024*1024},1024*1024+1,reader);reject({owned.data(),0,64},4,{});
    bool original=false;try{boundedRead({owned.data(),0,64},4,[](char*,size_t){throw std::runtime_error("original-read-failure");});}catch(const std::runtime_error&e){original=std::string(e.what())=="original-read-failure";}
    if(!original||reads!=1||refused!=8)throw std::runtime_error("Failure/read count differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":8,\"guard_bytes\":16,\"original_error_preserved\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
