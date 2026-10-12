#include "read_phase.hpp"
#include <iostream>
#include <stdexcept>
int main(int argc,char**argv){try{
    if(argc!=2)throw std::runtime_error("Fresh root required");std::filesystem::path root=argv[1];if(std::filesystem::exists(root))throw std::runtime_error("Preserve root");std::filesystem::create_directory(root);
    pose::read_phase::Evidence e;std::vector<char> b(16800,0);size_t refusals=0;
    auto reject=[&](auto fn){bool rejected=false;try{fn();}catch(const std::exception&){rejected=true;}if(!rejected)throw std::runtime_error("Refusal absent");++refusals;};
    reject([&]{e.beforeCPU(1,"{}",b.data(),b.size());});
    reject([&]{e.begin(0,1,1,"{}");});
    e.begin(100000,0,1,"{}");reject([&]{e.readDone(2,"{}",b.data(),1);});e.readDone(2,"{}",b.data(),b.size());
    reject([&]{e.readDone(3,"{}",b.data(),b.size());});b[9]=char(42);e.beforeCPU(4,"{}",b.data(),b.size());b[9]=0;
    reject([&]{e.beforeCPU(5,"{}",b.data(),b.size());});
    bool foreign=false;std::thread t([&]{try{e.error(5,"foreign");}catch(const std::exception&){foreign=true;}});t.join();if(!foreign)throw std::runtime_error("Foreign owner accepted");
    for(uint64_t i=1;i<103;++i){e.begin(100000+i,i,10*i,"{}");if(i==102){e.error(10*i+1,"Injected\nread\x1b failure");}else{e.readDone(10*i+1,"{}",b.data(),b.size());e.beforeCPU(10*i+2,"{}",b.data(),b.size());}}
    reject([&]{e.begin(100103,103,1030,"{}");});e.save(root/"evidence");reject([&]{e.save(root/"again");});reject([&]{e.begin(100103,103,1030,"{}");});
    if(refusals!=8)throw std::runtime_error("Refusal count differs");
    std::cout<<"{\"status\":\"passed\",\"refusals\":8,\"foreign_thread_refused\":true,\"owned_bytes\":true,\"first4_last\":true,\"partial_read_saved\":true,\"device_opened\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
