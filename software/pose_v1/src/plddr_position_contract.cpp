#include "plddr_position_contract.hpp"
#include <limits>
#include <stdexcept>
namespace pose::plddr_position {
namespace {
void need(bool v,const char*m){if(!v){throw std::runtime_error(m);}}
uint64_t end(uint64_t a,uint64_t bytes){need(bytes>0&&a<=std::numeric_limits<uint64_t>::max()-bytes,"Range empty or overflowing");return a+bytes;}
void contained(Pool p,Block b){need(b.identity!=0&&b.start>=p.start&&end(b.start,b.bytes)<=end(p.start,p.bytes),"Block outside public pool or missing identity");}
}
void validatePool(Pool p,const std::vector<Block>& initial){
    end(p.start,p.bytes);need(initial.empty(),"Pool not initially empty");
    need(p.start<=sourceLower&&end(p.start,p.bytes)>=sourceUpper&&p.bytes>=prefixBytes+30240+32+16800,"Public pool cannot cover candidate window");
}
void validateAllocated(Pool p,Block prefix,Block a,Block padding,Block b){
    const Block blocks[]{prefix,a,padding,b};for(const auto&v:blocks){contained(p,v);}
    need(prefix.bytes==prefixBytes&&a.bytes==30240&&padding.bytes==32&&b.bytes==16800,"Allocated sizes differ");
    for(unsigned i=0;i<4;++i){for(unsigned j=i+1;j<4;++j){need(blocks[i].identity!=blocks[j].identity&&(end(blocks[i].start,blocks[i].bytes)<=blocks[j].start||end(blocks[j].start,blocks[j].bytes)<=blocks[i].start),"Owned chunks alias or overlap");}}
    for(const auto&src:{a,b}){need(src.start%64==0&&src.start>=sourceLower&&end(src.start,src.bytes)<=sourceUpper,"Source position not controlled or alignment differs");}
}
}
