#pragma once
#include "fixed_filter.hpp"
#include "postprocess.hpp"
#include <chrono>
#include <functional>
#include <string>
#include <thread>
namespace pose::post {
// Caller owns all Device/MMIO access. Never probes r45 or guessed address mappings.
class PlFilter {
 std::function<std::uint32_t(unsigned)> read_;
 std::function<void(unsigned,std::uint32_t)> write_;
 std::uint32_t seq_=0;
public:
 PlFilter(std::string verified_profile,decltype(read_) read,decltype(write_) write):read_(read),write_(write){
  if(verified_profile!="pose-stabilizer-offline-v1")throw std::runtime_error("PL filter requires explicit new hardware identity");
  if(read_(0)!=0x504f5301)throw std::runtime_error("PL filter ABI mismatch");
 }
 std::array<std::int32_t,126> update(const std::array<std::int32_t,126>&values,double dt,unsigned init_mask,unsigned update_mask=7){
  const auto p=fixed::parameters(dt);if(read_(4)!=0)throw std::runtime_error("PL filter not idle/healthy");
  write_(0x1c,init_mask);write_(0x34,update_mask);write_(0x20,p.inverse_dt);write_(0x24,p.derivative_alpha);write_(0x28,p.k);write_(0x2c,p.min_cutoff);write_(0x30,p.beta);
  for(unsigned i=0;i<126;++i)write_(0x400+i*4,std::uint32_t(values[i]));
  write_(0xc,++seq_);write_(8,1);
  auto deadline=std::chrono::steady_clock::now()+std::chrono::milliseconds(2);
  while(read_(0x10)!=seq_){if((read_(4)&0xf0)||std::chrono::steady_clock::now()>=deadline)throw std::runtime_error("PL filter isolated; no retry");}
  if(read_(4)!=0)throw std::runtime_error("PL filter completed with error");
  std::array<std::int32_t,126> out{};for(unsigned i=0;i<126;++i)out[i]=std::int32_t(read_(0x800+4*i));return out;
 }
};
class PlFilterBackend final:public FilterBackend {
 PlFilter& hardware_;std::array<std::uint64_t,3> tracks_{};std::array<std::int32_t,126> inputs_{};
public:
 explicit PlFilterBackend(PlFilter& hardware):hardware_(hardware){}
 void reset() override {tracks_.fill(0);inputs_.fill(0);}
 void begin_frame(const std::vector<Person>& ps) override {
  for(auto& id:tracks_)if(std::none_of(ps.begin(),ps.end(),[&](const Person&p){return p.track==id;}))id=0;
 }
 Joints update(std::uint64_t track,const Joints& x,double dt,bool initialize) override {
  auto it=std::find(tracks_.begin(),tracks_.end(),track);
  if(it==tracks_.end()){it=std::find(tracks_.begin(),tracks_.end(),0);if(it==tracks_.end())throw std::runtime_error("PL slots exhausted");*it=track;initialize=true;}
  const unsigned slot=unsigned(it-tracks_.begin());
  for(unsigned i=0;i<42;++i)inputs_[slot*42+i]=fixed::q(x[i]);
  // Each person may have a different dt after missing frames. Other banks freeze.
  const auto out=hardware_.update(inputs_,dt,initialize?1u<<slot:0,1u<<slot);
  Joints result{};for(unsigned i=0;i<42;++i)result[i]=float(out[slot*42+i])/65536.f;return result;
 }
};
}
