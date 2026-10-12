#include "producer_read_contract.hpp"
#include <stdexcept>
namespace pose::producer_read {
namespace {void need(bool x){if(!x){throw std::runtime_error("Output read lease contract rejected");}}}
void validateSources(const std::array<Source,2>&s){
    constexpr uint64_t lower=104ULL*1024*1024,upper=105ULL*1024*1024;
    for(size_t i=0;i<2;++i){const auto&x=s[i];need(x.value==(i?4390:4386)&&x.bytes==(i?16800:30240)&&x.chunk_identity&&x.offset<=x.capacity&&x.bytes<=x.capacity-x.offset);
        need(x.address>=lower&&x.address<=upper&&x.bytes<=upper-x.address&&x.address%64==0);}
    need(s[0].chunk_identity!=s[1].chunk_identity);need(s[0].address+s[0].bytes<=s[1].address||s[1].address+s[1].bytes<=s[0].address);
    need(2*(s[0].bytes+s[1].bytes)<=1024*1024);
}
bool Guard::owner()const noexcept{return owner_==std::this_thread::get_id();}
void Guard::idle()const{need(owner()&&alive_&&!active_);}
uint64_t Guard::open(){idle();need(opened_<100);active_=true;++opened_;return ++token_;}
void Guard::check(uint64_t token)const{need(owner()&&alive_&&active_&&token==token_);}
void Guard::close(uint64_t token){check(token);active_=false;++closed_;}
void Guard::expire(){need(owner());if(active_){active_=false;++closed_;++forced_;}alive_=false;}
}
