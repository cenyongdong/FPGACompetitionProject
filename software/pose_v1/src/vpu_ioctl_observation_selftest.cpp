#include "vpu_ioctl_observation.hpp"
#include <linux/videodev2.h>
#include <cstdarg>
#include <cerrno>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
extern "C" int __wrap_ioctl(int,unsigned long,...);
namespace {void* expected;unsigned calls=0;int answer=0,fakeErrno=0;void need(bool v){if(!v){throw std::runtime_error("Observer transparency contract failed");}}}
extern "C" int __real_ioctl(int fd,unsigned long request,...){
    va_list a;va_start(a,request);void* p=va_arg(a,void*);va_end(a);need(fd==7&&p==expected);++calls;
    if(answer==0&&request==VIDIOC_DQBUF){static_cast<v4l2_buffer*>(p)->sequence=31;}
    errno=fakeErrno;return answer;
}
int main(int argc,char**argv){try{
    need(argc==2&&!std::filesystem::exists(argv[1]));std::filesystem::create_directory(argv[1]);
    v4l2_plane plane{};plane.bytesused=77;v4l2_buffer b{};b.type=V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE;b.index=1;b.length=1;b.m.planes=&plane;expected=&b;
    {pose::video_observation::Observer o;
        for(int error:{EINTR,EAGAIN,0}){answer=error?-1:0;fakeErrno=error;auto before=b;const auto result=__wrap_ioctl(7,VIDIOC_DQBUF,&b);need(result==answer&&errno==error&&plane.bytesused==77);if(error){need(std::memcmp(&before,&b,sizeof(b))==0);}else{need(b.sequence==31);}}
        auto before=b;answer=0;fakeErrno=EDOM;need(__wrap_ioctl(7,VIDIOC_QBUF,&b)==0&&errno==EDOM&&std::memcmp(&before,&b,sizeof(b))==0);
        need(__wrap_ioctl(7,VIDIOC_S_FMT,&b)==0&&errno==EDOM);o.finish(std::filesystem::path(argv[1])/"events.jsonl");}
    {pose::video_observation::Observer o(1);__wrap_ioctl(7,VIDIOC_QBUF,&b);__wrap_ioctl(7,VIDIOC_QBUF,&b);bool refused=false;try{o.check();}catch(const std::exception&){refused=true;}need(refused);}
    answer=-1;fakeErrno=EINTR;need(__wrap_ioctl(7,VIDIOC_QBUF,&b)==-1&&errno==EINTR);need(calls==8);
    std::cout<<"Observer pointer/metadata/return/errno/EINTR/EAGAIN/unknown/capacity/detach contracts passed.\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
