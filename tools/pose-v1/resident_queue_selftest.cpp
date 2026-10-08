#include "resident_frame_queue.hpp"
#include <cassert>
#include <thread>
#include <iostream>
int main(){
    using namespace pose::video;ResidentFrameQueue q;
    auto frame=[](unsigned id){OwnedFrame f;f.generatedNs=id;f.invocation=id;f.nv12.resize(nv12FrameBytes,uint8_t(id));return f;};
    q.publish(frame(1));q.publish(frame(2));q.publish(frame(3));
    auto second=q.pop(),third=q.pop();assert(second->invocation==2&&third->invocation==3&&!q.pop());
    assert(q.stats().overwritten==1&&q.stats().highWater==2);
    auto copy=*third;copy.nv12[0]=0;assert(third->nv12[0]==3);
    ResidentFrameQueue threaded;
    std::thread worker([&]{for(unsigned i=1;i<=20;++i)threaded.publish(frame(i));});worker.join();
    assert(threaded.stats().published==20&&threaded.stats().overwritten==18&&threaded.stats().highWater==2);
    assert(threaded.pop()->invocation==19&&threaded.pop()->invocation==20);
    threaded.publish(frame(21));threaded.publish(frame(22));assert(threaded.popLatest()->invocation==22);
    assert(threaded.stats().coalesced==1&&!threaded.popLatest());
    threaded.fail(std::make_exception_ptr(std::runtime_error("synthetic")));unsigned refused=0;
    for(unsigned i=0;i<3;++i)try{if(i==0)threaded.check();else if(i==1)threaded.pop();else threaded.publish(frame(21));}catch(const std::exception&){++refused;}
    assert(refused==3);q.stop();try{q.publish(frame(4));assert(false);}catch(const std::runtime_error&){}
    std::cout<<"Capacity2/overwrite/immutable-copy/thread-publication/failure/stop passed; no hardware\n";
}
