#include "tcp_receiver.hpp"
#include <arpa/inet.h>
#include <atomic>
#include <cerrno>
#include <cmath>
#include <cstring>
#include <exception>
#include <poll.h>
#include <stdexcept>
#include <sys/socket.h>
#include <thread>
#include <unistd.h>

namespace pose_v1::transport {
namespace {
void need(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
uint64_t le(const unsigned char* p,size_t n){uint64_t v=0;for(size_t i=0;i<n;++i)v|=uint64_t(p[i])<<(8*i);return v;}
void header(const std::vector<unsigned char>& data){need(data.size()>=32,"Truncated CSI header");need(std::memcmp(data.data(),"PIWCSI1\0",8)==0,"Invalid CSI magic");need(le(data.data()+8,4)==1 && le(data.data()+12,4)==kPayloadBytes,"Invalid CSI version/length");}
}
Window decode_record(const std::vector<unsigned char>& data){
    header(data);need(data.size()==record_bytes,"Truncated/trailing CSI payload");
    Window w;w.frame_id=le(data.data()+16,8);w.source_time_ns=le(data.data()+24,8);
    for(size_t i=0;i<kComplexCount;++i){double re,im;uint64_t a=le(data.data()+32+i*16,8),b=le(data.data()+40+i*16,8);
        std::memcpy(&re,&a,8);std::memcpy(&im,&b,8);need(std::isfinite(re)&&std::isfinite(im),"Non-finite raw CSI record");w.csi[i]={re,im};}
    return w;
}
bool LatestSlot::push(Item item){std::lock_guard<std::mutex> lock(mutex_);need(!closed_,"Push after receiver close");bool dropped=item_.has_value();item_=std::move(item);cv_.notify_one();return dropped;}
bool LatestSlot::clear(){std::lock_guard<std::mutex> lock(mutex_);bool dropped=item_.has_value();item_.reset();return dropped;}
void LatestSlot::close(){std::lock_guard<std::mutex> lock(mutex_);closed_=true;cv_.notify_all();}
std::optional<Item> LatestSlot::pop(std::chrono::milliseconds wait){std::unique_lock<std::mutex> lock(mutex_);cv_.wait_for(lock,wait,[&]{return item_||closed_;});auto result=std::move(item_);item_.reset();return result;}
bool LatestSlot::finished(){std::lock_guard<std::mutex> lock(mutex_);return closed_&&!item_;}
struct Receiver::Impl {
    LatestSlot slot;int listener=-1;std::atomic<int> connection{-1};std::atomic<bool> stopping{false};
    std::thread worker;std::mutex mutex;Stats counters;std::vector<std::string> messages;std::exception_ptr fatal;
    uint16_t bound_port=0;int idle_ms;size_t max_sessions;
    Impl(const std::string& address,uint16_t port,int idle,size_t limit):idle_ms(idle),max_sessions(limit){
        need(idle>=100 && idle<=60000,"Idle timeout outside 100..60000ms");
        listener=::socket(AF_INET,SOCK_STREAM,0);need(listener>=0,"TCP socket failed");
        try{sockaddr_in local{};local.sin_family=AF_INET;local.sin_port=htons(port);need(inet_pton(AF_INET,address.c_str(),&local.sin_addr)==1,"Invalid IPv4 bind address");
            // No reuse-port: an existing service must fail rather than share traffic.
            need(::bind(listener,reinterpret_cast<sockaddr*>(&local),sizeof(local))==0,"TCP bind failed");need(::listen(listener,1)==0,"TCP listen failed");
            socklen_t n=sizeof(local);need(getsockname(listener,reinterpret_cast<sockaddr*>(&local),&n)==0,"Bound port query failed");bound_port=ntohs(local.sin_port);
            worker=std::thread([this]{loop();});
        }catch(...){::close(listener);listener=-1;throw;}
    }
    enum class Read { Full, Eof, Stop };
    Read exact(int fd,std::vector<unsigned char>& bytes,size_t first,size_t last){
        size_t pos=first;auto deadline=Clock::now()+std::chrono::milliseconds(idle_ms);
        while(pos<last){if(stopping)return Read::Stop;pollfd p{fd,POLLIN,0};int ready=::poll(&p,1,100);
            if(ready<0){if(errno==EINTR)continue;throw std::runtime_error("TCP receive poll failed");}
            if(ready==0){need(Clock::now()<deadline,"TCP record idle timeout");continue;}
            ssize_t n=::recv(fd,bytes.data()+pos,last-pos,0);
            if(n==0){need(pos==first && first==0,"Connection interrupted inside record");return Read::Eof;}
            if(n<0){if(errno==EINTR)continue;if(stopping)return Read::Stop;throw std::runtime_error("TCP receive failed");}
            pos+=size_t(n);deadline=Clock::now()+std::chrono::milliseconds(idle_ms);
        }return Read::Full;
    }
    void loop(){
        try{while(!stopping){pollfd p{listener,POLLIN,0};int ready=::poll(&p,1,100);if(stopping)break;
            if(ready<0){if(errno==EINTR)continue;throw std::runtime_error("TCP accept poll failed");}if(!ready)continue;
            int fd=::accept(listener,nullptr,nullptr);if(fd<0&&stopping)break;need(fd>=0,"TCP accept failed");connection=fd;
            uint64_t session;{std::lock_guard<std::mutex> lock(mutex);session=++counters.sessions;if(slot.clear())++counters.reconnect_discarded;}
            try{bool first=true;uint64_t last=0;std::vector<unsigned char> bytes(record_bytes);
                while(!stopping){auto status=exact(fd,bytes,0,32);if(status!=Read::Full)break;header(bytes);
                    status=exact(fd,bytes,32,bytes.size());if(status==Read::Stop)break;
                    // Stamp completion before payload decoding, not after inference starts.
                    auto arrived=Clock::now();auto w=decode_record(bytes);need(first||w.frame_id>last,"Non-monotonic frame id in session");first=false;last=w.frame_id;
                    std::lock_guard<std::mutex> lock(mutex);Item item{std::move(w),session,counters.received++,arrived};if(slot.push(std::move(item)))++counters.overwritten;
                }
            }catch(const std::exception& e){if(!stopping){std::lock_guard<std::mutex> lock(mutex);++counters.rejected;if(messages.size()<16)messages.push_back(e.what());}}
            // Keep current fd published until close, preventing stop from using a reused fd.
            {std::lock_guard<std::mutex> lock(mutex);::close(fd);connection=-1;}
            if(max_sessions && session>=max_sessions)break;
        }}catch(...){std::lock_guard<std::mutex> lock(mutex);fatal=std::current_exception();}
        slot.close();
    }
    void stop(){stopping=true;std::lock_guard<std::mutex> lock(mutex);if(listener>=0)::shutdown(listener,SHUT_RDWR);int fd=connection.load();if(fd>=0)::shutdown(fd,SHUT_RDWR);}
    ~Impl(){stop();if(worker.joinable())worker.join();if(listener>=0)::close(listener);}
};
Receiver::Receiver(const std::string& a,uint16_t p,int idle,size_t n):p_(std::make_unique<Impl>(a,p,idle,n)){}
Receiver::~Receiver()=default;
std::optional<Item> Receiver::pop(std::chrono::milliseconds t){return p_->slot.pop(t);}
bool Receiver::finished(){return p_->slot.finished();}
Stats Receiver::stats(){std::lock_guard<std::mutex> lock(p_->mutex);return p_->counters;}
std::vector<std::string> Receiver::errors(){std::lock_guard<std::mutex> lock(p_->mutex);return p_->messages;}
uint16_t Receiver::port()const{return p_->bound_port;}
void Receiver::stop(){p_->stop();}
void Receiver::check(){std::lock_guard<std::mutex> lock(p_->mutex);if(p_->fatal)std::rethrow_exception(p_->fatal);}
}
