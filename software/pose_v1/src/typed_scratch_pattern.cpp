#include "typed_scratch_pattern.hpp"
#include <cstring>
#include <stdexcept>
namespace pose::typed_scratch {
Bytes pattern(size_t slot,size_t index){
    if(slot>=2||index>maximumPattern){throw std::runtime_error("Typed scratch pattern identity differs");}
    if(index==0){return pose::scratch::pattern(slot);}
    Bytes result(pose::scratch::sizes[slot]);
    for(size_t i=0;i<result.size()/4;++i){
        const float value=slot?float(100000+index*8192+i):float(index*8192+i)+0.25f;
        std::memcpy(result.data()+i*4,&value,4);
    }
    return result;
}
bool matches(const Pair& pair,size_t index){
    if(index>maximumPattern){throw std::runtime_error("Typed comparison index exceeds budget");}
    bool result=true;
    for(size_t i=0;i<2;++i){
        if(pair.values[i].size()!=pose::scratch::sizes[i]){throw std::runtime_error("Typed comparison bytes differ");}
        result=result&&(pair.values[i]==pattern(i,index));
    }
    return result;
}
void saveExpected(size_t index,const std::filesystem::path& directory){
    Pair expected;for(size_t i=0;i<2;++i){expected.values[i]=pattern(i,index);}
    pose::scratch::savePair(expected,directory);
}
}
