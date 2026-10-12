#include "vpu_ioctl_observation.hpp"
#include <linux/videodev2.h>
#include <atomic>
#include <array>
#include <cstdarg>
#include <cerrno>
#include <chrono>
#include <fstream>
#include <mutex>
#include <stdexcept>
#include <thread>
extern "C" int __real_ioctl(int,unsigned long,...);
namespace pose::video_observation {
namespace {
struct Event {uint64_t begin=0,end=0,thread=0;unsigned long request=0;int fd=0,result=0,error=0;unsigned type=0,index=0,flags=0,sequence=0,bytes=0;int64_t pts=0;};
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
std::atomic<Observer::Impl*> active{nullptr};
void snapshot(Event&e,const v4l2_buffer& b){
    e.type=b.type;e.index=b.index;e.flags=b.flags;e.sequence=b.sequence;e.pts=b.timestamp.tv_sec*1000000LL+b.timestamp.tv_usec;
    if((b.type==V4L2_BUF_TYPE_VIDEO_OUTPUT_MPLANE||b.type==V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE)&&b.m.planes&&b.length<=VIDEO_MAX_PLANES){for(unsigned i=0;i<b.length;++i){e.bytes+=b.m.planes[i].bytesused;}}
}
}
struct Observer::Impl {
    std::array<Event,8192> events{};size_t count=0,limit;mutable std::mutex mutex;std::atomic<bool> failed{false};uint64_t writer=0;bool attached=true;
    explicit Impl(size_t n):limit(n){if(n==0||n>events.size()){throw std::runtime_error("Observer bound invalid");}}
    void record(const Event&e)noexcept{try{
        std::lock_guard<std::mutex> lock(mutex);
        if(writer&&writer!=e.thread){failed=true;return;}writer=e.thread;
        if(count==limit){failed=true;return;}events[count++]=e;
    }catch(...){failed=true;}}
};
Observer::Observer(size_t n):p_(std::make_unique<Impl>(n)){
    Impl* expected=nullptr;if(!active.compare_exchange_strong(expected,p_.get())){throw std::runtime_error("Observer already active");}
}
Observer::~Observer(){if(p_->attached){active.store(nullptr);}}
void Observer::check()const{if(p_->failed.load()){throw std::runtime_error("Observer capacity/thread contract failed");}}
void Observer::finish(const std::filesystem::path&out){
    // Caller must join the sole VPU writer before detach/save.
    active.store(nullptr);p_->attached=false;
    if(std::filesystem::exists(out)){throw std::runtime_error("Preserve observer evidence");}
    std::ofstream f(out);
    for(size_t i=0;i<p_->count;++i){const auto&e=p_->events[i];f<<"{\"ordinal\":"<<i<<",\"request\":\""<<(e.request==VIDIOC_QBUF?"QBUF":"DQBUF")<<"\",\"begin_ns\":"<<e.begin<<",\"end_ns\":"<<e.end<<",\"thread\":"<<e.thread<<",\"fd\":"<<e.fd<<",\"return\":"<<e.result<<",\"errno_at_return\":"<<e.error<<",\"type\":"<<e.type<<",\"index\":"<<e.index<<",\"flags\":"<<e.flags<<",\"sequence\":"<<e.sequence<<",\"bytesused\":"<<e.bytes<<",\"pts_us\":"<<e.pts<<"}\n";}
    f.close();if(!f){throw std::runtime_error("Observer save failed");}check();
}
}
extern "C" int __wrap_ioctl(int fd,unsigned long request,...){
    // All audited static callers pass exactly one pointer, including unknown
    // V4L2 operations. No no-argument ioctl exists in the linked VPU source.
    va_list args;va_start(args,request);void* argument=va_arg(args,void*);va_end(args);
    using namespace pose::video_observation;
    auto* state=active.load();const bool observe=state&&(request==VIDIOC_QBUF||request==VIDIOC_DQBUF)&&argument;
    Event e;
    if(observe){e.fd=fd;e.request=request;e.thread=std::hash<std::thread::id>{}(std::this_thread::get_id());snapshot(e,*static_cast<v4l2_buffer*>(argument));e.begin=now();}
    const int result=__real_ioctl(fd,request,argument);const int savedErrno=errno;
    if(observe){e.end=now();e.result=result;e.error=savedErrno;
        if(result>=0){e.bytes=0;snapshot(e,*static_cast<v4l2_buffer*>(argument));}state->record(e);}
    errno=savedErrno;return result;
}
