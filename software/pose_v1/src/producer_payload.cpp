#include "producer_payload.hpp"
#include <cmath>
#include <cstring>
#include <fstream>
#include <stdexcept>
namespace pose::producer {
void need(bool c,const char* m){if(!c){throw std::runtime_error(m);}}
Bytes readFile(const std::filesystem::path&p,size_t size){
    need(std::filesystem::file_size(p)==size,"Payload file byte count differs");
    std::ifstream f(p,std::ios::binary);Bytes bytes(size);f.read(bytes.data(),size);
    need(bool(f),"Payload read incomplete");return bytes;
}
void saveFile(const std::filesystem::path&p,const Bytes& bytes){
    need(!std::filesystem::exists(p),"Preserve previous output");
    std::ofstream f(p,std::ios::binary);f.write(bytes.data(),bytes.size());f.close();need(bool(f),"Output save incomplete");
}
void saveText(const std::filesystem::path&p,const std::string&s){saveFile(p,Bytes(s.begin(),s.end()));}
std::string text(const std::filesystem::path&p){
    const auto n=std::filesystem::file_size(p);need(n<=1024*1024,"Text too large");auto b=readFile(p,n);return std::string(b.begin(),b.end());
}
uint64_t fingerprint(const Bytes& bytes){uint64_t h=14695981039346656037ULL;for(unsigned char b:bytes){h^=b;h*=1099511628211ULL;}return h;}
void validate(const Payload&p){
    for(size_t s=0;s<2;++s){need(p.inputs[s].size()==inputSizes[s]&&p.expected[s].size()==outputSizes[s],"Payload sizes differ");}
    for(size_t i=0;i<100;++i){float v;std::memcpy(&v,p.inputs[0].data()+4*i,4);need(std::isfinite(v)&&v>=0&&v<180&&std::floor(v)==v,"Invalid actual integer index");}
    for(size_t i=0;i<p.inputs[1].size()/2;++i){uint16_t v;std::memcpy(&v,p.inputs[1].data()+2*i,2);need((v&0x7c00)!=0x7c00,"Nonfinite FP16 input");}
    for(const auto& b:p.expected){for(size_t i=0;i<b.size()/4;++i){float v;std::memcpy(&v,b.data()+4*i,4);need(std::isfinite(v),"Nonfinite reference output");}}
}
Payload load(const std::filesystem::path&p){
    Payload v;v.inputs={readFile(p/"input-486.f32",400),readFile(p/"input-478.f16",17280)};
    v.expected={readFile(p/"output-4386.f32",30240),readFile(p/"output-4390.f32",16800)};validate(v);return v;
}
void compareSaved(const std::filesystem::path&p,const Payload& reference){
    // Both complete outputs must already be on disk before any comparison.
    Pair actual{readFile(p/"output-4386.f32",30240),readFile(p/"output-4390.f32",16800)};
    for(const auto& b:actual){for(size_t i=0;i<b.size()/4;++i){float v;std::memcpy(&v,b.data()+4*i,4);need(std::isfinite(v),"Saved physical output nonfinite");}}
    need(actual==reference.expected,"Saved physical outputs differ from independent reference");
}
}
