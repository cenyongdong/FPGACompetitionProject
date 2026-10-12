#include "scratch_copy_pattern.hpp"
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{namespace s=pose::scratch;namespace fs=std::filesystem;auto need=[](bool ok){if(!ok)throw std::runtime_error("Scratch pattern test failed");};need(argc==2&&!fs::exists(argv[1]));fs::path out=argv[1];fs::create_directory(out);unsigned refuses=0;auto reject=[&](auto fn){try{fn();}catch(const std::exception&){++refuses;return;}throw std::runtime_error("Missing scratch rejection");};
    s::Pair valid;for(size_t i=0;i<2;++i){auto producer=s::pattern(i);valid.values[i]=s::own(producer.data(),producer.size());producer.assign(producer.size(),0);}need(s::matches(valid));s::savePair(valid,out/"owned");
    reject([&]{s::pattern(2);});reject([&]{s::own(nullptr,s::sizes[0]);});reject([&]{s::own(valid.values[0].data(),0);});reject([&]{s::own(valid.values[0].data(),s::sizes[0]-1);});reject([&]{s::fingerprint({});});reject([&]{s::Pair p;s::matches(p);});reject([&]{s::Pair p;s::savePair(p,out/"wrong");});reject([&]{s::savePair(valid,out/"owned");});
    auto bad=valid;bad.values[1][5]^=1;need(!s::matches(bad));s::savePair(bad,out/"one-bit-bad");bad=valid;for(size_t i=3040*4;i<3056*4;++i)bad.values[1][i]=valid.values[0][i];need(!s::matches(bad));s::savePair(bad,out/"previous-copy-block");
    std::cout<<"{\"status\":\"passed\",\"refusals\":"<<refuses<<",\"owned_bytes\":47760,\"bit_mismatch_detected\":true,\"previous_copy_block_detected\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
