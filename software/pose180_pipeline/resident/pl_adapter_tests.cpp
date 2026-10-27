#include "pl_filter.hpp"
#include "lean_admission.hpp"
#include <iostream>
#include <map>
using namespace pose::post;
int main(){try{
 unsigned reads=0;std::map<unsigned,std::uint32_t> regs{{0,0x504f5301},{4,0}};
 std::array<fixed::State,126> memory{};bool first=true;
 auto rd=[&](unsigned a){++reads;return regs[a];};
 auto wr=[&](unsigned a,std::uint32_t v){regs[a]=v;if(a==8&&v==1){
  fixed::Parameters p{std::int32_t(regs[0x20]),std::int32_t(regs[0x24]),std::int32_t(regs[0x28]),std::int32_t(regs[0x2c]),std::int32_t(regs[0x30])};
  for(unsigned i=0;i<126;++i){bool init=first||((regs[0x1c]>>(i/42))&1),update=first||((regs[0x34]>>(i/42))&1);
   if(update)fixed::step(memory[i],std::int32_t(regs[0x400+4*i]),p,init);regs[0x800+4*i]=memory[i].y;}
  first=false;regs[0x10]=regs[0xc];}};
 bool refused=false;try{PlFilter bad("r45",rd,wr);}catch(...){refused=true;}
 if(!refused||reads)throw std::runtime_error("Wrong profile probed hardware");
 regs[0x18]=4;PlFilter hw("probe-free-drain-filter-v1",rd,wr);
 if(hw.lanes()!=4||verify_pl_filter(hw)!=3024)throw std::runtime_error("New profile self-test failed");
 regs[0]=0;refused=false;try{PlFilter bad("probe-free-drain-filter-v1",rd,wr);}catch(const PlFilterError&){refused=true;}
 if(!refused)throw std::runtime_error("Mismatched ABI accepted");regs[0]=0x504f5301;
 PlFilterBackend backend(hw);Postprocessor a,b({},&backend);
 std::array<float,180> scores{};std::array<float,7560> coords{};std::uint64_t ns=1000000000;double max_error=0;
 for(unsigned f=0;f<40;++f){ns+=(f%3==0?110:f%3==1?67:61)*1000000ull;scores.fill(0);
  for(unsigned person=0;person<3;++person){if(person==1&&(f==6||f==7))continue;scores[person]=.8f;
   for(unsigned j=0;j<14;++j){coords[person*42+j*3]=person*2+.02f*std::sin(f*.2f);coords[person*42+j*3+1]=j*.1f;coords[person*42+j*3+2]=(j%2)*.2f;}}
  Identity id{f<25?1u:2u,f+1,f+1,ns};auto x=a.update(id,scores.data(),coords.data()),y=b.update(id,scores.data(),coords.data());
  if(x.poses.size()!=y.poses.size())throw std::runtime_error("Backend changed lifecycle");
  for(unsigned k=0;k<x.poses.size();++k)for(unsigned j=0;j<42;++j)max_error=std::max(max_error,double(std::abs(x.poses[k].joints[j]-y.poses[k].joints[j])));
 }
 if(max_error>.001)throw std::runtime_error("Per-person PL dt/slot mismatch");
 // Exercise identity handoff with real filter bank state; equality of lifecycle
 // alone would miss a reset or slot mix-up. Extended retention is CPU-only.
 backend.reset();Postprocessor hc,hp({},&backend);std::uint64_t hs=1,ht=1000000000;
 auto compare=[&](double position,unsigned candidate,bool missing,unsigned ms){
  ht+=std::uint64_t(ms)*1000000;scores.fill(0);if(!missing)scores[candidate]=.8f;
  for(unsigned j=0;j<14;++j){coords[candidate*42+j*3]=float(position+.05*(int(j%3)-1));coords[candidate*42+j*3+1]=float(.1*(int(j%2)-1));coords[candidate*42+j*3+2]=float(.15*j);}
  Identity id{10,hs,hs,ht};++hs;auto x=hc.update(id,scores.data(),coords.data()),y=hp.update(id,scores.data(),coords.data());
  if(x.poses.size()!=y.poses.size())throw std::runtime_error("Handoff backend changed lifecycle");
  for(unsigned k=0;k<x.poses.size();++k){if(x.poses[k].track!=y.poses[k].track||x.poses[k].held!=y.poses[k].held)throw std::runtime_error("Handoff backend changed identity");
   for(unsigned j=0;j<42;++j)max_error=std::max(max_error,double(std::abs(x.poses[k].joints[j]-y.poses[k].joints[j])));}
 };
 for(unsigned k=0;k<12;++k)compare(.15*(int(k)-11),0,false,67);
 compare(-.4,0,false,67);for(unsigned k=0;k<3;++k)compare(-.88,9,false,67);
 if(hc.metrics().held_handoffs!=1||hp.metrics().held_handoffs!=1||max_error>.001)throw std::runtime_error("Handoff filter state mismatch");
 const auto reads_before=reads;refused=false;
 try{std::array<std::int32_t,126> sample{};hw.update(sample,.367,0);}catch(const PlFilterError&){refused=true;}
 if(!refused||reads!=reads_before)throw std::runtime_error("Unsupported long interval accessed PL");
 regs[4]=0x10;refused=false;
 try{std::array<std::int32_t,126> sample{};hw.update(sample,.067,7);}catch(const PlFilterError&){refused=true;}
 if(!refused)throw std::runtime_error("Hardware failure not isolated");
 b.set_backend(nullptr);ns+=67000000;
 if(!b.update({2,41,41,ns},scores.data(),coords.data()).poses.empty())throw std::runtime_error("CPU fallback reused partially filtered state");
 regs[4]=0;
 LeanReceipt receipt;receipt.abi=0x4c534701;receipt.state=4;receipt.request=receipt.response=1;receipt.native_dependency_present=true;
 if(lean_admitted(receipt,"pose-stabilizer-offline-v1"))throw std::runtime_error("Missing coverage admitted");
 receipt.coverage_complete=true;receipt.native_history[2]=1u<<15;
 if(lean_admitted(receipt,"pose-stabilizer-offline-v1"))throw std::runtime_error("r9 bit79 admitted");
 receipt.native_history={};if(lean_admitted(receipt,"r45"))throw std::runtime_error("r8 legacy evidence reinterpreted");
 std::map<unsigned,std::uint32_t> guard{{4,0x4c534701},{0x40,4},{0x40+27*4,1},{0x40+28*4,1}};
 LeanGuard client("pose-stabilizer-offline-v1",[&](unsigned a){return guard[a];},[&](unsigned a,std::uint32_t v){if(a||v)throw std::runtime_error("Unexpected hardware command in snapshot test");guard[12]=++guard[8];});
 if(!lean_admitted(client.request(0).receipt,"pose-stabilizer-offline-v1"))throw std::runtime_error("Snapshot decode");
 guard[0x40+19*4]=1u<<15;if(lean_admitted(client.request(0).receipt,"pose-stabilizer-offline-v1"))throw std::runtime_error("Snapshot lost native79");
 guard[0]=1;refused=false;try{client.request(1);}catch(...){refused=true;}if(!refused)throw std::runtime_error("Busy guard command accepted");
 std::cout<<"PL_ADAPTER_PASS max_error="<<max_error<<"\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
