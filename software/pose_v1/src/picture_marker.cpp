#include "picture_source.hpp"
#include <algorithm>
#include <sstream>
#include <iomanip>
namespace pose::picture {
void markEncodedId(std::vector<uint8_t>& image,unsigned id){
    // Ten bits cover the bounded1000-frame stream, below all known joints.
    for(unsigned y=600;y<680;++y)std::fill(image.begin()+y*1280+40,image.begin()+y*1280+1240,16);
    for(unsigned y=300;y<340;++y)std::fill(image.begin()+1280*720+y*1280+40,image.begin()+1280*720+y*1280+1240,128);
    for(unsigned bit=0;bit<10;++bit)for(unsigned y=604;y<632;++y)
        std::fill(image.begin()+y*1280+44+bit*64,image.begin()+y*1280+84+bit*64,id&(1u<<bit)?235:16);
}
std::string frameHash(const std::vector<uint8_t>& bytes){
    uint64_t hash=14695981039346656037ULL;for(auto byte:bytes){hash^=byte;hash*=1099511628211ULL;}
    std::ostringstream out;out<<std::hex<<std::setw(16)<<std::setfill('0')<<hash;return out.str();
}
}
