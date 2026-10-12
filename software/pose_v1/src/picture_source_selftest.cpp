#include "picture_source.hpp"
#include <iostream>
#include <stdexcept>
namespace {void need(bool b,const char*s){if(!b){throw std::runtime_error(s);}}}
int main(){try{
    namespace v=pose::video;namespace p=pose::picture;unsigned refusals=0;
    auto reject=[&](auto f){try{f();}catch(const std::exception&){++refusals;return;}throw std::runtime_error("Missing picture refusal");};
    auto warm=[](){v::OwnedFrame f;f.nv12.assign(v::nv12FrameBytes,80);f.generatedNs=1;f.inferenceResult=false;return f;};
    auto real=[&](uint64_t id){auto f=warm();f.invocation=id;f.sourceFrame=100000+id;f.generatedNs=2+id;f.inferenceResult=true;f.nv12[0]=uint8_t(id+20);return f;};
    p::Source s(warm());auto a=s.sample(0,1);need(a&&!a->frame.inferenceResult,"NoInput missing");
    auto f=real(0);s.publish(f);f.nv12[0]=0;auto b=s.sample(1,1);need(b&&b->frame.nv12[0]==20&&!b->frame.repeatedSource,"Publication did not own bytes");
    b->frame.nv12[0]=0;auto c=s.sample(2,1);auto expected=real(0).nv12;p::markEncodedId(expected,2);need(c&&c->frame.nv12==expected&&c->frame.repeatedSource,"Repeat mutated cached bytes");
    s.publish(real(1));s.publish(real(2));s.publish(real(3));auto d=s.sample(3,1);auto q=s.stats();need(d->frame.invocation==3&&q.overwritten==1&&q.coalesced==1&&q.highWater==2,"Capacity2 latest policy differs");
    s.publish(real(4));s.stop();auto last=s.sample(4,1);need(last&&last->frame.invocation==4&&!s.sample(5,1),"Normal drain lost pending last frame");reject([&]{s.publish(real(5));});
    reject([&]{auto w=warm();w.nv12.pop_back();p::Source invalid(w);});
    reject([&]{p::Source t(warm());t.publish(real(1));});
    reject([&]{p::Source t(warm());auto r=real(0);r.sourceFrame=100001;t.publish(r);});
    reject([&]{p::Source t(warm());auto r=real(0);r.inferenceResult=false;t.publish(r);});
    reject([&]{p::Source t(warm());t.sample(1000,1);});
    reject([&]{p::Source t(warm());t.sample(0,0);});
    p::Source failed(warm());failed.fail(std::make_exception_ptr(std::runtime_error("Original error")));reject([&]{failed.sample(0,1);});reject([&]{failed.publish(real(0));});reject([&]{failed.check();});
    p::Source full(warm());for(uint64_t i=0;i<107;++i){full.publish(real(i));need(full.sample(unsigned(i),1)->frame.invocation==i,"Full source identity differs");}reject([&]{full.publish(real(107));});
    bool refused=false;p::Source owner(warm());std::thread other([&]{try{owner.publish(real(0));}catch(const std::exception&){refused=true;}});other.join();need(refused,"Producer changed owner");++refusals;
    bool consumerRefused=false;owner.sample(0,1);std::thread consumer([&]{try{owner.sample(1,1);}catch(const std::exception&){consumerRefused=true;}});consumer.join();need(consumerRefused,"Consumer changed owner");++refusals;
    std::cout<<"{\"status\":\"passed\",\"refusals\":"<<refusals<<",\"calls\":107,\"capacity\":2,\"owns_publication\":true,\"immutable_repeat\":true,\"overwrite_oldest\":true,\"coalesces_latest\":true,\"drains_last_pending\":true,\"owner_checked\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
