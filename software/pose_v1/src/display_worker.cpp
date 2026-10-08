// SDK-free executable. Receives values, calls the frozen renderer, returns owned NV12.
#include "display_protocol.hpp"
#include "skeleton_render.hpp"
#include <filesystem>
#include <fstream>
#include <iostream>
#include <unistd.h>
#include <cmath>
#include <stdexcept>

namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
int main(int argc,char** argv){try{
    using namespace pose::display;namespace rr=pose_v1::render;
    need(argc==3&&std::string(argv[1])=="3","Display worker fd contract differs");const int fd=3;const std::filesystem::path out=argv[2];
    std::ofstream log(out/"child.jsonl"),fds(out/"child-fds.txt");need(bool(log)&&bool(fds),"Display child evidence failed");
    for(const auto& entry:std::filesystem::directory_iterator("/proc/self/fd")){std::error_code error;auto target=std::filesystem::read_symlink(entry.path(),error);if(!error){fds<<entry.path().filename().string()<<' '<<target.string()<<'\n';need(target.string().find("/dev/video")==std::string::npos&&target.string().find("udmabuf")==std::string::npos&&target.string().find("/dev/mem")==std::string::npos,"Display inherited device descriptor");}}fds.close();
    wire::writeHeader(fd,{wire::Kind::Ready,0,uint64_t(::getpid()),0,wire::now()});size_t renders=0;
    // First request may wait for parent's VPU first-capture + bounded Engine init.
    while(true){auto h=wire::readHeader(fd,{},70000);
        if(h.kind==wire::Kind::Stop){wire::writeHeader(fd,{wire::Kind::Stopped});break;}
        need(h.kind==wire::Kind::Render&&renders<33,"Display request kind/budget differs");
        Pose p;p.frame=h.frame;p.invocation=h.invocation;p.publishedNs=h.begin;wire::read(fd,p.scores.data(),sizeof(p.scores));wire::read(fd,p.poses.data(),sizeof(p.poses));validate(p);
        const auto begin=wire::now();auto rgb=rr::draw(p.scores,p.poses,p.frame);const auto drawn=wire::now();
        for(const auto& point:rgb.projected)need(point[1]<590,"Display joint overlaps marker");
        auto pixels=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);const auto converted=wire::now();need(pixels.size()==nv12Bytes,"Display renderer byte count differs");
        wire::writeHeader(fd,{wire::Kind::Image,nv12Bytes,p.frame,p.invocation,begin,drawn,converted});wire::write(fd,pixels.data(),pixels.size());
        log<<"{\"invocation\":"<<p.invocation<<",\"frame_id\":"<<p.frame<<",\"begin_ns\":"<<begin<<",\"draw_end_ns\":"<<drawn<<",\"convert_end_ns\":"<<converted<<"}\n";++renders;
    }
    log<<"{\"event\":\"stopped\",\"renders\":"<<renders<<",\"SDK\":false,\"VPU\":false}"<<std::endl;::close(fd);return 0;
}catch(const std::exception& e){std::cerr<<"DISPLAY_STOP: "<<e.what()<<'\n';return 1;}}
