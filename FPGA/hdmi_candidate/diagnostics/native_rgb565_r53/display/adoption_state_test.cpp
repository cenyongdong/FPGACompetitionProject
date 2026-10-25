// SDK-free state-machine tests only. No fake SDK or hardware success claim.
#include "adoption_state.hpp"
#include <array>
#include <iostream>
#include <stdexcept>
using pose::hdmi::detail::AdoptionSample;
using pose::hdmi::detail::AdoptionState;
namespace {
unsigned checks=0;
void need(bool ok,const char* why){++checks;if(!ok)throw std::runtime_error(why);}
template<class F>void refuses(F action){bool rejected=false;try{action();}catch(const std::exception&){rejected=true;}need(rejected,"Unsafe state was accepted");}
constexpr uint32_t a=0x31100000,b=0x314f4800;
constexpr int64_t first_deadline=200001000;
AdoptionSample idle(){return {0xc1,0,0,0,0};}
AdoptionSample accepted(uint32_t id,uint32_t address,uint32_t status=0x142,uint32_t stopped=0,uint32_t faults=0){return {status,stopped,address,id,faults};}
struct MockBuffers {
 AdoptionState state;std::array<unsigned,2>writes{};
 void begin(uint32_t id,uint32_t address,const AdoptionSample& prior,int64_t deadline=first_deadline){
  const auto slot=state.next_slot(id);state.reserve(slot,id,address,prior,100);
  ++writes[slot]; // Ordinary-memory ownership token, not an SDK call.
  state.wait_after_command(deadline);
 }
};
AdoptionState waiting(){AdoptionState s;s.reserve(0,1,a,idle(),100);s.wait_after_command(first_deadline);return s;}
}
int main(){try{
 MockBuffers buffers;need(!buffers.state.poll(idle(),0),"Idle poll should be false");
 buffers.begin(1,a,idle());need(buffers.state.pending(),"Submission reservation absent");
 refuses([&]{buffers.begin(2,b,idle());});need(buffers.writes[0]==1&&buffers.writes[1]==0,"Pending buffer was reused");
 need(!buffers.state.poll({0x52,0,0,0,0},1000),"Old frame was mistaken for new adoption");
 need(!buffers.state.poll(accepted(1,a,0x152),2000),"Pending flag ignored");
 need(!buffers.state.buffers_releasable(),"Unstopped frames marked releasable");
 need(buffers.state.poll(accepted(1,a),first_deadline-1),"Timely matching adoption refused");
 need(!buffers.state.pending()&&buffers.state.current_slot()==0,"Adopted slot did not become current");
 refuses([&]{buffers.state.next_slot(1);});need(buffers.state.next_slot(2)==1,"Next frame would overwrite active slot");
 buffers.begin(2,b,accepted(1,a),400000100);
 need(!buffers.state.poll(accepted(1,a),300000100),"Previous frame released the reservation");
 need(buffers.state.current_slot()==0&&buffers.writes[0]==1&&buffers.writes[1]==1,"Buffer ownership changed before proof");
 need(buffers.state.poll(accepted(2,b),399999999),"Second adoption refused");
 need(buffers.state.next_slot(3)==0,"Proved former buffer not available");
 for(auto bad:{accepted(1,a,0x142,0,8),accepted(1,a,0x102),accepted(9,a),accepted(1,b),accepted(1,a,0x142,7),accepted(1,a,0x1c1)}){
  auto s=waiting();refuses([&]{s.poll(bad,1000);});need(s.pending()&&!s.buffers_releasable(),"Failure lost its ownership hold");
  refuses([&]{s.next_slot(2);});
 }
 for(auto time:{first_deadline,first_deadline+1}){
  auto s=waiting();refuses([&]{s.poll(accepted(1,a),time);});
  need(s.pending()&&!s.buffers_releasable(),"Late match released a buffer");
 }
 {auto s=waiting();refuses([&]{s.poll({0x52,0,0,0,0},first_deadline);});}
 {auto s=waiting();refuses([&]{s.wait_after_command(first_deadline+200000000);});
  need(s.deadline_ns()==first_deadline,"Poll/reset renewed the deadline");}
 // The deadline is anchored after command ACK, not before the SDK write.
 {AdoptionState s;s.reserve(0,1,a,idle(),100);s.wait_after_command(250000100);
  need(s.poll(accepted(1,a),250000099),"Post-command deadline anchor moved before write");}
 {auto s=waiting();refuses([&]{s.prove_stop({1,8,0,0,0},9);});
  refuses([&]{s.prove_stop({0x11,9,0,0,0},9);});need(!s.buffers_releasable(),"Bad/busy STOP permitted release");
  s.prove_stop({0x81,9,0,0,8},9); // Fault/PLL loss does not defeat an independent safe STOP.
  need(s.buffers_releasable()&&!s.pending(),"Valid STOP did not release ownership hold");
  refuses([&]{s.next_slot(2);});refuses([&]{s.poll(accepted(1,a),1000);});}
 {AdoptionState s;s.reserve(0,1,a,idle(),100);s.fail();
  need(s.pending()&&!s.waiting(),"Uncertain write/command was automatically rearmed");
  refuses([&]{s.next_slot(2);});refuses([&]{s.poll(accepted(1,a),1000);});
  s.prove_stop({1,9,0,0,0},9);need(s.buffers_releasable(),"Failed submission could not be safely closed");}
 {AdoptionState s;refuses([&]{s.reserve(1,1,a,idle(),100);});}
 {AdoptionState s;refuses([&]{s.reserve(0,1,0,idle(),100);});}
 std::cout<<"{\"SDK_free\":true,\"SDK\":0,\"MMIO\":0,\"checks\":"<<checks<<",\"passed\":true,\"scope\":\"logical ownership and caller-observed adoption state only\"}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<"\n";return 2;}}
