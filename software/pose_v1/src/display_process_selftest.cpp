#include "display_process.hpp"
#include "display_queue.hpp"
#include "skeleton_render.hpp"
#include <sys/wait.h>
#include <signal.h>
#include <cstring>
#include <limits>
#include <iostream>
#include <fstream>
#include <thread>

namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
int main(int argc,char** argv){try{
    using namespace pose::display;namespace fs=std::filesystem;namespace rr=pose_v1::render;
    need(argc==3,"display selftest WORKER FRESH-OUTPUT");fs::path out=argv[2];need(!fs::exists(out),"Preserve display selftest");fs::create_directory(out);
    Pose pose;pose.frame=11;pose.publishedNs=wire::now();pose.scores[0]=1;
    for(size_t i=0;i<pose.poses.size();i+=3){pose.poses[i]=1.5f;pose.poses[i+1]=1.75f;pose.poses[i+2]=3.4f;}
    unsigned refused=0;auto reject=[&](auto function){try{function();}catch(const std::exception&){++refused;return;}throw std::runtime_error("Expected display refusal missing");};
    wire::Header h{wire::Kind::Render,poseBytes,11,0,pose.publishedNs};auto bytes=wire::encode(h);need(wire::decode(bytes).bytes==poseBytes,"Display header roundtrip differs");
    auto broken=bytes;broken[0]^=1;reject([&]{wire::decode(broken);});broken=bytes;broken[20]=1;reject([&]{wire::decode(broken);});broken=bytes;broken[16]^=1;reject([&]{wire::decode(broken);});broken=bytes;broken[12]=99;reject([&]{wire::decode(broken);});
    auto bad=pose;bad.scores[0]=std::numeric_limits<float>::infinity();reject([&]{validate(bad);});
    Queue queue;for(size_t i=0;i<3;++i){pose.invocation=i;queue.publish(pose);}pose.scores[0]=.5f;auto owned=queue.next();need(owned->scores[0]==1&&owned->invocation==2,"Display queue ownership/selection differs");auto q=queue.stats();need(q.published==3&&q.overwritten==1&&q.coalesced==1&&q.adopted==1&&q.highWater==2,"Display queue counts differ");
    queue.close();need(!queue.next(),"Display close not drained");reject([&]{queue.publish(pose);});
    Queue failed;failed.fail(std::make_exception_ptr(std::runtime_error("intentional")));reject([&]{failed.next();});
    Queue blocked;bool woke=false;std::thread waiter([&]{try{blocked.next();}catch(const std::exception&){woke=true;}});blocked.fail(std::make_exception_ptr(std::runtime_error("wake")));waiter.join();need(woke,"Display failure did not wake waiter");
    uint64_t bytesChecked=0;Process process(argv[1],out/"normal");const int child=process.pid();need(child>0,"Display child identity missing");
    for(size_t i=0;i<3;++i){pose.invocation=i;pose.frame=11+i;pose.publishedNs=wire::now();auto image=process.render(pose);auto rgb=rr::draw(pose.scores,pose.poses,pose.frame);auto expected=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);need(image.nv12==expected,"Display IPC image differs");bytesChecked+=image.nv12.size();}
    auto first=process.render(pose);auto kept=first.nv12;pose.frame=15;pose.publishedNs=wire::now();auto second=process.render(pose);need(first.nv12==kept&&second.frame==15,"Display returned ownership differs");bytesChecked+=first.nv12.size()+second.nv12.size();process.finish();int status=0;need(::waitpid(child,&status,WNOHANG)<0&&errno==ECHILD,"Display child not reaped");
    {Process killed(argv[1],out/"killed");need(::kill(killed.pid(),SIGKILL)==0,"Selftest owned child kill failed");reject([&]{killed.render(pose);});}
    {Process cancelled(argv[1],out/"cancelled");reject([&]{cancelled.render(pose,[]{return true;});});}
    std::cout<<"{\"status\":\"passed\",\"rejections\":"<<refused<<",\"IPC_NV12_bytes\":"<<bytesChecked<<",\"capacity\":2,\"one_request_credit\":true,\"owned_bytes\":true,\"reaped\":true,\"SDK_device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
