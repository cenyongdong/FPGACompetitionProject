#pragma once
#include <algorithm>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace pose::validation {
// Diagnostic image marker; does not alter the pose or renderer projection.
inline void markEncodedFrame(std::vector<uint8_t>& nv12,unsigned id){
    if(nv12.size()!=1280*720*3/2||id>=1000)throw std::runtime_error("Frame marker contract invalid");
    for(unsigned y=600;y<680;++y)std::fill(nv12.begin()+y*1280+40,nv12.begin()+y*1280+1240,16);
    for(unsigned y=300;y<340;++y)std::fill(nv12.begin()+1280*720+y*1280+40,nv12.begin()+1280*720+y*1280+1240,128);
    for(unsigned bit=0;bit<10;++bit)for(unsigned y=604;y<632;++y)
        std::fill(nv12.begin()+y*1280+44+bit*64,nv12.begin()+y*1280+84+bit*64,id&(1u<<bit)?235:16);
}
}
