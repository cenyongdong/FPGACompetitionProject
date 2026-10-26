// Reads retained complete records only. No SDK, network, or device API.
#include "postprocess.hpp"
#include "wire.hpp"
#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <chrono>
#include <cmath>
using namespace pose::post;
int main(int argc,char**argv){try{
 if(argc<2)throw std::runtime_error("Usage: pose_replay recent-*.full > replay.ndjson");
 using Raw=std::array<unsigned char,pose180_pipeline::full_bytes>;
 std::map<std::uint64_t,Raw> records;
 for(int i=1;i<argc;++i){std::ifstream in(argv[i],std::ios::binary);if(!in)throw std::runtime_error("Cannot open raw ring");Raw b{};
  while(in.read(reinterpret_cast<char*>(b.data()),b.size())){
   if(std::memcmp(b.data(),"PIWFUL3\0",8)||pose180_pipeline::get32(b.data()+8)!=3||pose180_pipeline::get32(b.data()+12)!=b.size())throw std::runtime_error("Invalid raw record");
   auto seq=pose180_pipeline::get64(b.data()+72);auto it=records.find(seq);if(it!=records.end()&&it->second!=b)throw std::runtime_error("Conflicting raw sequence");records[seq]=b;
  }if(in.gcount())throw std::runtime_error("Truncated raw record");
 }
 Postprocessor p;unsigned raw_changes=0,shown_changes=0,last_raw=0,last_shown=0,raw_jumps=0,track_jumps=0;bool first=true;
 PresentationFrame previous;double total_ms=0,max_ms=0;
 auto distance=[](const Person&a,const Person&b){double sum=0;for(unsigned axis=0;axis<3;++axis){double d=0;for(unsigned j=0;j<14;++j)d+=(a.joints[j*3+axis]-b.joints[j*3+axis])/14.;sum+=d*d;}return std::sqrt(sum);};
 for(const auto&entry:records){const auto&b=entry.second;Identity id{pose180_pipeline::get64(b.data()+16),pose180_pipeline::get64(b.data()+24),entry.first,pose180_pipeline::get64(b.data()+40)};
  std::array<float,180>s{};std::array<float,7560>v{};std::memcpy(s.data(),b.data()+43584,sizeof(s));std::memcpy(v.data(),b.data()+44304,sizeof(v));auto start=std::chrono::steady_clock::now();auto f=p.update(id,s.data(),v.data());
  double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();total_ms+=ms;max_ms=std::max(max_ms,ms);
  for(unsigned i=0;i<std::min(previous.raw_poses.size(),f.raw_poses.size());++i)raw_jumps+=distance(previous.raw_poses[i],f.raw_poses[i])>.5;
  for(const auto&a:previous.poses)for(const auto&b:f.poses)if(a.track==b.track&&!b.held)track_jumps+=distance(a,b)>.5;
  if(!first){raw_changes+=last_raw!=f.raw_poses.size();shown_changes+=last_shown!=f.poses.size();}first=false;last_raw=unsigned(f.raw_poses.size());last_shown=unsigned(f.poses.size());std::cout<<f.json(true);previous=f;
 }
 const auto&m=p.metrics();std::cerr<<"{\"records\":"<<records.size()<<",\"raw_count_changes\":"<<raw_changes<<",\"shown_count_changes\":"<<shown_changes<<",\"births\":"<<m.births<<",\"expired\":"<<m.expired<<",\"deduplicated\":"<<m.duplicates<<",\"rejected_pairs\":"<<m.rejected_pairs<<",\"raw_rank_jumps_gt_0_5\":"<<raw_jumps<<",\"stable_track_jumps_gt_0_5\":"<<track_jumps<<",\"mean_compute_ms\":"<<total_ms/std::max(std::size_t(1),records.size())<<",\"max_compute_ms\":"<<max_ms<<",\"mean_confirmation_ms\":"<<m.confirmation_total_ns/1e6/std::max(std::uint64_t(1),m.births)<<",\"max_confirmation_ms\":"<<m.confirmation_max_ns/1e6<<",\"ground_truth\":false}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
