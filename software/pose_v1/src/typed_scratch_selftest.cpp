#include "typed_scratch_pattern.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <functional>
#include <iostream>
#include <set>
#include <stdexcept>
namespace ts=pose::typed_scratch;
int main(int argc,char**argv){try{
    if(argc!=2||std::filesystem::exists(argv[1])){throw std::runtime_error("Fresh typed contract directory required");}
    const std::filesystem::path out=argv[1];std::filesystem::create_directory(out);
    unsigned refusals=0;
    auto reject=[&](const std::function<void()>& test){bool bad=false;try{test();}catch(const std::exception&){bad=true;}if(!bad){throw std::runtime_error("Invalid contract accepted");}++refusals;};
    ts::Pair first,last;
    std::set<uint64_t> fingerprints;
    for(size_t index=0;index<=100;++index){
        ts::Pair current;
        for(size_t slot=0;slot<2;++slot){
            current.values[slot]=ts::pattern(slot,index);
            if(index==0&&current.values[slot]!=pose::scratch::pattern(slot)){throw std::runtime_error("Constant baseline changed");}
            for(size_t i=0;i<current.values[slot].size()/4;++i){float value;std::memcpy(&value,current.values[slot].data()+i*4,4);
                const double expected=slot?double(100000+index*8192+i):double(index*8192+i)+.25;
                if(!std::isfinite(value)||double(value)!=expected){throw std::runtime_error("FP32 pattern not exact");}
            }
            if(!fingerprints.insert(pose::scratch::fingerprint(current.values[slot])).second){throw std::runtime_error("Pattern fingerprints repeated");}
        }
        if(!ts::matches(current,index)){throw std::runtime_error("Own pattern mismatch");}
        if(index==0){first=current;}if(index==100){last=current;}
    }
    reject([&]{ts::pattern(2,0);});reject([&]{ts::pattern(0,101);});reject([&]{ts::matches(first,101);});
    reject([&]{auto p=first;p.values[1].pop_back();ts::matches(p,0);});
    if(ts::matches(first,1)||ts::matches(last,99)){throw std::runtime_error("Stale generation accepted");}
    auto bad=last;std::copy(first.values[0].begin()+256,first.values[0].begin()+384,bad.values[1].begin()+256);
    if(ts::matches(bad,100)){throw std::runtime_error("Previous-copy block accepted");}
    pose::scratch::savePair(first,out/"pattern0");pose::scratch::savePair(last,out/"pattern100");pose::scratch::savePair(bad,out/"previous-copy-block");
    ts::Pair partial;partial.values[0]=last.values[0];pose::scratch::saveAvailable(partial,out/"partial");
    reject([&]{pose::scratch::saveAvailable(partial,out/"partial");});reject([&]{auto p=partial;p.values[0].resize(1);pose::scratch::saveAvailable(p,out/"invalid-partial");});
    reject([&]{pose::scratch::own(nullptr,30240);});reject([&]{pose::scratch::own(first.values[0].data(),1);});
    if(refusals!=8){throw std::runtime_error("Refusal count differs");}
    std::cout<<"{\"status\":\"passed\",\"refusals\":8,\"patterns\":101,\"unique_slot_fingerprints\":202,\"FP32_exact\":true,\"partial_saved\":true,\"stale_generation_rejected\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
