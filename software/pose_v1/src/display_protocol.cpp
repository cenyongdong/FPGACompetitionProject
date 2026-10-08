#include "display_protocol.hpp"
#include <chrono>
#include <cmath>
#include <cstring>
#include <cerrno>
#include <poll.h>
#include <sys/socket.h>
#include <stdexcept>

namespace pose::display {
namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
void validate(const Pose& p){
    need(p.frame&&p.publishedNs,"Display identity/time missing");
    for(float v:p.scores)need(std::isfinite(v),"Display score nonfinite");
    for(float v:p.poses)need(std::isfinite(v),"Display pose nonfinite");
}
namespace wire {
namespace {
void put(Bytes& b,size_t at,uint64_t v,size_t n){for(size_t i=0;i<n;++i)b[at+i]=v>>(8*i);}
uint64_t get(const Bytes& b,size_t at,size_t n){uint64_t v=0;for(size_t i=0;i<n;++i)v|=uint64_t(b[at+i])<<(8*i);return v;}
void size(const Header& h){
    need(h.kind==Kind::Ready||h.kind==Kind::Render||h.kind==Kind::Image||h.kind==Kind::Stop||h.kind==Kind::Stopped,"Display message kind invalid");
    need(h.bytes==(h.kind==Kind::Render?poseBytes:h.kind==Kind::Image?nv12Bytes:0),"Display payload length invalid");
}
void exact(int fd,void* p,size_t length,bool sending,const Cancel& cancel,unsigned timeoutMs=5000){
    need(length<=nv12Bytes&&timeoutMs>=1&&timeoutMs<=70000,"Display transfer exceeds fixed bounds");auto* bytes=static_cast<unsigned char*>(p);size_t offset=0;const auto deadline=now()+uint64_t(timeoutMs)*1000000;
    while(offset<length){
        need(!cancel||!cancel(),"Display transfer cancelled");need(now()<deadline,"Display IPC deadline exceeded");
        pollfd item{fd,short(sending?POLLOUT:POLLIN),0};int ready=::poll(&item,1,50);
        if(ready<0&&errno==EINTR)continue;
        need(ready>=0&&!(item.revents&POLLNVAL),"Display IPC poll failure");if(!ready)continue;
        ssize_t n=sending?::send(fd,bytes+offset,length-offset,MSG_NOSIGNAL): ::recv(fd,bytes+offset,length-offset,0);
        if(n<0&&(errno==EINTR||errno==EAGAIN||errno==EWOULDBLOCK))continue;
        need(n>0,"Display IPC closed/failed inside message");offset+=size_t(n);
    }
}
}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
Bytes encode(const Header& h){
    size(h);uint16_t endian=1;need(*reinterpret_cast<unsigned char*>(&endian)==1&&sizeof(float)==4,"Display FP32 little-endian contract differs");
    Bytes b{};std::memcpy(b.data(),"PIWDSP1\0",8);put(b,8,1,4);put(b,12,uint32_t(h.kind),4);put(b,16,h.bytes,4);
    put(b,24,h.frame,8);put(b,32,h.invocation,8);put(b,40,h.begin,8);put(b,48,h.drawEnd,8);put(b,56,h.convertEnd,8);return b;
}
Header decode(const Bytes& b){
    need(std::memcmp(b.data(),"PIWDSP1\0",8)==0&&get(b,8,4)==1&&get(b,20,4)==0,"Display header identity/reserved invalid");
    Header h{Kind(get(b,12,4)),uint32_t(get(b,16,4)),get(b,24,8),get(b,32,8),get(b,40,8),get(b,48,8),get(b,56,8)};size(h);return h;
}
void write(int fd,const void* p,size_t n,const Cancel& c){exact(fd,const_cast<void*>(p),n,true,c);}
void read(int fd,void* p,size_t n,const Cancel& c){exact(fd,p,n,false,c);}
void writeHeader(int fd,const Header& h,const Cancel& c){const auto b=encode(h);write(fd,b.data(),b.size(),c);}
Header readHeader(int fd,const Cancel& c,unsigned idleMs){Bytes b;exact(fd,b.data(),b.size(),false,c,idleMs);return decode(b);}
}
}
