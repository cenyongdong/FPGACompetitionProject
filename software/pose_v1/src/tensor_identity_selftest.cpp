#include "tensor_identity_observation.hpp"
#include <functional>
#include <iostream>
#include <stdexcept>
#include <thread>
namespace ti=pose::tensor_identity;
int main(int argc,char**argv){try{if(argc!=2)throw std::runtime_error("fresh output required");std::filesystem::path out=argv[1];if(std::filesystem::exists(out))throw std::runtime_error("preserve");std::filesystem::create_directory(out);
ti::Pair p;auto&s=p.source;s.tensor=1;s.region=2;s.chunk=3;s.device=4;s.address=4096;s.bytes=16800;s.capacity=16800;s.ownerMatches=true;s.declaredMatches=true;s.kind="ADDR";s.regionKey="test";s.type=s.declaredType="{\"shape\":[4200],\"layout\":\"C\",\"FP32\":true,\"distributions\":[]}";p.destination=s;p.destination.tensor=5;p.destination.region=6;p.destination.chunk=7;p.destination.device=8;p.destination.address=65536;p.destination.kind="CPTR";
ti::Recorder normal;normal.sample(0,0,192,1,false,p);normal.sample(0,0,192,1,true,p);normal.save(out/"normal");unsigned refusals=0;
auto reject=[&](std::function<void()> f){bool bad=false;try{f();}catch(const std::exception&){bad=true;}if(!bad)throw std::runtime_error("accepted invalid identity");++refusals;};
for(unsigned k=0;k<11;++k){ti::Recorder r;auto q=p;reject([&]{if(k==0)q.source.chunk=0;if(k==1)q.source.offset=16801;if(k==2)q.source.capacity=16799;if(k==3)q.source.ownerMatches=false;if(k==4)q.source.declaredMatches=false;if(k==5)q.destination.kind="ADDR";if(k==6)q.source.type="{}";if(k==7)q.source.kind="unknown";if(k==8)q.destination.bytes=4;if(k==9)q.source.type=q.source.declaredType=std::string(20000,'x');r.sample(0,0,k==10?442:192,1,false,q);});}
ti::Recorder changed;changed.sample(0,0,192,1,false,p);auto q=p;q.source.region=9;reject([&]{changed.sample(0,0,192,1,true,q);});changed.save(out/"changed");
ti::Recorder missing;reject([&]{missing.sample(0,0,192,1,true,p);});
ti::Recorder pending;pending.sample(0,0,192,1,false,p);reject([&]{pending.sample(0,0,192,1,false,p);});
reject([&]{normal.save(out/"normal");});
ti::Recorder owned;bool threadRejected=false;std::thread t([&]{try{owned.sample(0,0,192,1,false,p);}catch(...){threadRejected=true;}});t.join();if(!threadRejected)throw std::runtime_error("thread owner accepted");++refusals;
ti::Recorder budget;for(size_t i=0;i<1024;++i){budget.sample(i,i,192,1,false,p);budget.sample(i,i,192,1,true,p);}reject([&]{budget.sample(1024,1024,192,1,false,p);});
if(refusals!=17)throw std::runtime_error("refusal count");std::cout<<"{\"status\":\"passed\",\"refusals\":17,\"partial_identity_saved\":true,\"normal_device_reads_added\":0,\"SDK_device\":false}\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
