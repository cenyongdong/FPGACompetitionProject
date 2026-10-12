#include "producer_address_contract.hpp"
#include <limits>
#include <stdexcept>
#include <set>
namespace pose::producer_address {
namespace {
void need(bool x){if(!x){throw std::runtime_error("Address layout contract failed");}}
uint64_t end(Block b){need(b.bytes&&b.start<=std::numeric_limits<uint64_t>::max()-b.bytes);return b.start+b.bytes;}
void inside(Pool p,Block b){need(b.identity&&b.start>=p.start&&end(b)<=end({p.start,p.bytes,1}));}
}
void validatePool(Pool p,const std::vector<Block>&existing){need(p.start==4096&&p.bytes==4294963200ULL&&existing.empty());need(end({p.start,p.bytes,1})>upper);}
void validatePrefix(Pool p,Block b){inside(p,b);need(b.start==p.start&&b.bytes==prefixBytes&&b.start%4096==0);}
void validateMap(Pool p,Block prefix,const std::vector<Block>&blocks){
    validatePrefix(p,prefix);std::set<uint64_t> identities;unsigned match=0;
    for(size_t i=0;i<blocks.size();++i){const auto b=blocks[i];inside(p,b);need(identities.insert(b.identity).second);
        if(b.identity==prefix.identity){need(b.start==prefix.start&&b.bytes==prefix.bytes);++match;}
        else{need(b.start>=end(prefix)&&end(b)<=upper);}
        for(size_t j=0;j<i;++j){need(end(b)<=blocks[j].start||end(blocks[j])<=b.start);}}
    need(match==1);
}
void validateBoundary(Block b){need(b.identity&&b.bytes&&b.start%64==0&&b.start>=lower&&end(b)<=upper);}
}
