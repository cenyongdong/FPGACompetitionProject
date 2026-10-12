#include "scratch_copy_pattern.hpp"
#include <cstring>
#include <fstream>
#include <stdexcept>
namespace pose::scratch {
namespace {void need(bool ok,const char*why){if(!ok)throw std::runtime_error(why);}}
Bytes pattern(size_t slot){need(slot<2,"Scratch pattern slot differs");Bytes result(sizes[slot]);for(size_t i=0;i<result.size()/4;++i){float value=slot?float(100000+i):float(i)+0.25f;std::memcpy(result.data()+i*4,&value,4);}return result;}
Bytes own(const char* pointer,size_t bytes){need(pointer&&(bytes==sizes[0]||bytes==sizes[1]),"Scratch shadow pointer/size differs");Bytes result(bytes);std::memcpy(result.data(),pointer,bytes);return result;}
uint64_t fingerprint(const Bytes& bytes){need(bytes.size()==sizes[0]||bytes.size()==sizes[1],"Scratch hash size differs");uint64_t hash=14695981039346656037ULL;for(unsigned char c:bytes){hash^=c;hash*=1099511628211ULL;}return hash;}
bool matches(const Pair& pair){bool same=true;for(size_t i=0;i<2;++i){need(pair.values[i].size()==sizes[i],"Scratch pair size differs");same=same&&pair.values[i]==pattern(i);}return same;}
void saveAvailable(const Pair& pair,const std::filesystem::path& dir){
    for(size_t i=0;i<2;++i)need(pair.values[i].empty()||pair.values[i].size()==sizes[i],"Scratch partial pair size differs");
    need(!dir.empty()&&!std::filesystem::exists(dir),"Preserve partial scratch pair");std::filesystem::create_directory(dir);std::ofstream index(dir/"identity.json");
    index<<"{\"source\":\"owned_bytes\",\"partial\":"<<(pair.values[0].empty()||pair.values[1].empty()?"true":"false")<<",\"slots\":[";bool first=true;
    for(size_t i=0;i<2;++i){if(pair.values[i].empty())continue;const auto name=std::string(i?"b.f32":"a.f32");std::ofstream f(dir/name,std::ios::binary);f.write(pair.values[i].data(),pair.values[i].size());f.close();need(bool(f),"Scratch partial bytes save failed");
        if(!first)index<<',';
        first=false;index<<"{\"slot\":"<<i<<",\"bytes\":"<<sizes[i]<<",\"fnv1a64\":"<<fingerprint(pair.values[i])<<",\"file\":\""<<name<<"\"}";
    }index<<"]}\n";index.close();need(bool(index),"Scratch partial index failed");
}
void savePair(const Pair& pair,const std::filesystem::path& dir){for(size_t i=0;i<2;++i)need(pair.values[i].size()==sizes[i],"Scratch saved pair size differs");need(!dir.empty()&&!std::filesystem::exists(dir),"Preserve scratch pair");std::filesystem::create_directory(dir);std::ofstream index(dir/"identity.json");index<<"{\"source\":\"owned_bytes\",\"slots\":[";for(size_t i=0;i<2;++i){const auto name=std::string(i?"b.f32":"a.f32");std::ofstream f(dir/name,std::ios::binary);f.write(pair.values[i].data(),pair.values[i].size());f.close();need(bool(f),"Scratch pair save failed");if(i)index<<',';index<<"{\"slot\":"<<i<<",\"bytes\":"<<sizes[i]<<",\"fnv1a64\":"<<fingerprint(pair.values[i])<<",\"file\":\""<<name<<"\"}";}index<<"]}\n";index.close();need(bool(index),"Scratch pair index failed");}
}
