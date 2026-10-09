#include "bounded_load_contract.hpp"
#include "display_process.hpp"
#include "skeleton_render.hpp"
#include <sys/wait.h>
#include <iostream>
#include <stdexcept>
namespace {void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}}
int main(int argc,char** argv){try{
    namespace load=pose::bounded_load;namespace d=pose::display;namespace fs=std::filesystem;namespace rr=pose_v1::render;
    need(argc==3&&!fs::exists(argv[2]),"bounded-selftest WORKER FRESH-OUTPUT");fs::path out=argv[2];fs::create_directory(out);
    unsigned refusals=0;auto reject=[&](auto f){try{f();}catch(const std::exception&){++refusals;return;}throw std::runtime_error("Expected bounded refusal missing");};
    for(size_t i=0;i<103;++i)need(load::fixtureIndex(100000+i)==i%27,"103 mapping differs");
    reject([&]{load::fixtureIndex(99999);});reject([&]{load::fixtureIndex(100103);});
    reject([&]{load::keepReference(103,103,false);});reject([&]{load::keepReference(0,104,true);});
    size_t kept=0;for(size_t i=0;i<103;++i)kept+=load::keepReference(i,103,i<27);need(kept==29,"Sparse first/repeat/last coverage differs");
    d::Pose p;p.scores[0]=1;for(size_t i=0;i<p.poses.size();i+=3){p.poses[i]=1.5f;p.poses[i+1]=1.75f;p.poses[i+2]=3.4f;}
    auto exercise=[&](const char* name,bool overflow){d::Process worker(argv[1],out/name);const int pid=worker.pid();
        for(size_t i=0;i<103;++i){p.frame=100000+i;p.invocation=i;p.publishedNs=d::wire::now();auto image=worker.render(p);
            need(image.frame==p.frame&&image.invocation==i&&image.nv12.size()==d::nv12Bytes,"103 worker identity differs");
            if(i==0||i==102){auto rgb=rr::draw(p.scores,p.poses,p.frame);need(image.nv12==rr::yuv420sp(rgb.rgb,rr::width,rr::height,false),"Boundary IPC bytes differ");}}
        if(overflow){p.invocation=103;p.frame=100103;p.publishedNs=d::wire::now();reject([&]{worker.render(p);});}
        else{worker.finish();int status=0;need(::waitpid(pid,&status,WNOHANG)<0&&errno==ECHILD,"Bounded worker not reaped");}};
    exercise("normal",false);exercise("overflow",true);
    std::cout<<"{\"status\":\"passed\",\"mapping\":103,\"renders\":206,\"refusals\":"<<refusals<<",\"sparse_references\":29,\"SDK_device\":false}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
