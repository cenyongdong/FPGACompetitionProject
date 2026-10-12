#include "picture_source.hpp"
#include <chrono>
#include <algorithm>
#include <stdexcept>
namespace pose::picture {
namespace {
void need(bool ok,const char*why){if(!ok){throw std::runtime_error(why);}}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
}
Source::Source(pose::video::OwnedFrame warmup){
    need(!warmup.inferenceResult&&warmup.nv12.size()==pose::video::nv12FrameBytes&&warmup.generatedNs,"Invalid NoInput frame");
    latest_=std::make_shared<const pose::video::OwnedFrame>(std::move(warmup));
}
void Source::publish(pose::video::OwnedFrame frame){
    need(producer_==std::this_thread::get_id(),"Picture producer owner changed");
    need(next_<107&&frame.invocation==next_&&frame.sourceFrame==100000+next_&&frame.inferenceResult,"Picture source order or budget differs");
    queue_.publish(std::move(frame));++next_;
}
std::optional<pose::video::ResidentSample> Source::sample(unsigned id,uint64_t sampled){
    need(id<1000&&sampled,"Picture sample identity differs");
    const auto owner=std::this_thread::get_id();if(!consumer_){consumer_=owner;}
    need(*consumer_==owner,"Picture consumer owner changed");queue_.check();
    auto next=queue_.popLatest();
    if(next){latest_=std::move(next);}else if(queue_.stopped()){return {};}
    auto frame=*latest_;frame.encodedId=id;frame.repeatedSource=frame.inferenceResult&&previousReal_&&frame.invocation==previous_;
    previous_=frame.invocation;previousReal_=frame.inferenceResult;markEncodedId(frame.nv12,id);
    return pose::video::ResidentSample{std::move(frame),std::max(sampled,now())};
}
void Source::stop(){queue_.stop();}
void Source::fail(std::exception_ptr error){queue_.fail(error);}
void Source::check()const{queue_.check();}
pose::video::FrameQueueStats Source::stats()const{return queue_.stats();}
}
