// Retained complete records only. No SDK, network, or device API.
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
 if(argc<2)throw std::runtime_error("Usage: pose_replay [--identity-ms=250] recent-*.full > replay.ndjson");
 using Raw=std::array<unsigned char,pose180_pipeline::full_bytes>;
 std::map<std::uint64_t,Raw> records;Config config;
 for(int i=1;i<argc;++i){
  const std::string arg=argv[i];
  if(arg.rfind("--identity-ms=",0)==0){
   const auto ms=std::stoull(arg.substr(14));if(ms<250||ms>1000)throw std::runtime_error("Identity interval out of range");
   config.identity_ns=ms*1000000;continue;
  }
  std::ifstream in(arg,std::ios::binary);if(!in)throw std::runtime_error("Cannot open raw ring");Raw b{};
  while(in.read(reinterpret_cast<char*>(b.data()),b.size())){
   if(std::memcmp(b.data(),"PIWFUL3\0",8)||pose180_pipeline::get32(b.data()+8)!=3||pose180_pipeline::get32(b.data()+12)!=b.size())throw std::runtime_error("Invalid raw record");
   auto seq=pose180_pipeline::get64(b.data()+72);auto it=records.find(seq);
   if(it!=records.end()&&it->second!=b)throw std::runtime_error("Conflicting raw sequence");records[seq]=b;
  }
  if(in.gcount())throw std::runtime_error("Truncated raw record");
 }
 Postprocessor p(config);unsigned raw_changes=0,shown_changes=0,last_raw=0,last_shown=0,raw_jumps=0,track_jumps=0;
 unsigned id_switches=0,id_switch_jumps=0,near_pairs=0,near_held_pairs=0,blank_with_candidates=0;
 std::array<unsigned,4> shown_counts{};bool first=true;PresentationFrame previous;double total_ms=0,max_ms=0,max_id_switch=0;
 auto centre=[](const Person&a){std::array<double,3> c{};for(unsigned j=0;j<14;++j)for(unsigned k=0;k<3;++k)c[k]+=a.joints[j*3+k]/14.;return c;};
 auto radius=[&](const Person&a){auto c=centre(a);double sum=0;for(unsigned j=0;j<42;++j)sum+=std::pow(a.joints[j]-c[j%3],2);return std::max(.25,std::sqrt(sum/14));};
 auto distance=[&](const Person&a,const Person&b){auto x=centre(a),y=centre(b);double sum=0;for(unsigned k=0;k<3;++k)sum+=std::pow(x[k]-y[k],2);return std::sqrt(sum);};
 for(const auto&entry:records){
  const auto&b=entry.second;Identity id{pose180_pipeline::get64(b.data()+16),pose180_pipeline::get64(b.data()+24),entry.first,pose180_pipeline::get64(b.data()+40)};
  std::array<float,180>s{};std::array<float,7560>v{};
  std::memcpy(s.data(),b.data()+43584,sizeof(s));std::memcpy(v.data(),b.data()+44304,sizeof(v));
  const auto start=std::chrono::steady_clock::now();auto f=p.update(id,s.data(),v.data());
  const double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();total_ms+=ms;max_ms=std::max(max_ms,ms);
  for(unsigned i=0;i<std::min(previous.raw_poses.size(),f.raw_poses.size());++i)raw_jumps+=distance(previous.raw_poses[i],f.raw_poses[i])>.5;
  for(const auto&a:previous.poses)for(const auto&b:f.poses)if(a.track==b.track&&!b.held)track_jumps+=distance(a,b)>.5;
  // Visible replacement is not true identity accuracy. Exclude archive holes,
  // recovery epochs and long input gaps from the adjacent replacement metric.
  if(id.session==previous.id.session&&id.sequence==previous.id.sequence+1&&id.source_ns>previous.id.source_ns&&
     id.source_ns-previous.id.source_ns<=250000000&&previous.poses.size()==1&&f.poses.size()==1&&previous.poses[0].track!=f.poses[0].track){
   const double d=distance(previous.poses[0],f.poses[0]);++id_switches;id_switch_jumps+=d>.5;max_id_switch=std::max(max_id_switch,d);
  }
  for(unsigned a=0;a<f.poses.size();++a)for(unsigned b=0;b<a;++b)
   if(distance(f.poses[a],f.poses[b])<std::max(radius(f.poses[a]),radius(f.poses[b]))){++near_pairs;near_held_pairs+=f.poses[a].held||f.poses[b].held;}
  ++shown_counts[f.poses.size()];blank_with_candidates+=f.poses.empty()&&!f.raw_poses.empty();
  if(!first){raw_changes+=last_raw!=f.raw_poses.size();shown_changes+=last_shown!=f.poses.size();}
  first=false;last_raw=unsigned(f.raw_poses.size());last_shown=unsigned(f.poses.size());std::cout<<f.json(true);previous=f;
 }
 const auto&m=p.metrics();std::cerr<<'{';bool comma=false;
 auto emit=[&](const char*key,auto value){if(comma)std::cerr<<',';comma=true;std::cerr<<'"'<<key<<"\":"<<value;};
 emit("records",records.size());emit("identity_ms",config.identity_ns/1000000);
 emit("raw_count_changes",raw_changes);emit("shown_count_changes",shown_changes);emit("births",m.births);emit("expired",m.expired);
 emit("deduplicated",m.duplicates);emit("rejected_pairs",m.rejected_pairs);emit("display_duplicates",m.display_duplicates);
 emit("history_selections",m.history_selections);emit("reacquired",m.reacquired);emit("held_handoffs",m.held_handoffs);emit("hidden_frames",m.hidden_frames);
 emit("shadow_deferred",m.shadow_deferred);
 emit("raw_rank_jumps_gt_0_5",raw_jumps);emit("stable_track_jumps_gt_0_5",track_jumps);
 emit("adjacent_singleton_id_switches",id_switches);emit("adjacent_singleton_id_jumps_gt_0_5",id_switch_jumps);emit("max_adjacent_singleton_id_jump",max_id_switch);
 emit("near_pairs_centre_lt_radius",near_pairs);emit("near_held_pairs",near_held_pairs);emit("blank_with_candidates",blank_with_candidates);
 emit("shown_0",shown_counts[0]);emit("shown_1",shown_counts[1]);emit("shown_2",shown_counts[2]);emit("shown_3",shown_counts[3]);
 emit("mean_compute_ms",total_ms/std::max(std::size_t(1),records.size()));emit("max_compute_ms",max_ms);
 emit("mean_confirmation_ms",m.confirmation_total_ns/1e6/std::max(std::uint64_t(1),m.births));emit("max_confirmation_ms",m.confirmation_max_ns/1e6);
 emit("cpu_filter_frames",m.cpu_filter_frames);emit("cpu_filter_coordinates",m.cpu_filter_coordinates);emit("cpu_filter_total_ns",m.cpu_filter_ns);
 emit("cpu_filter_mean_us",m.cpu_filter_ns/1000./std::max(std::uint64_t(1),m.cpu_filter_frames));emit("cpu_filter_max_us",m.cpu_filter_max_ns/1000.);
 std::cerr<<",\"ground_truth\":false}\n";
 }catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
