// Tests production invocation ownership and timed input queue, no SDK/board.
#include "joint/display_flight.hpp"
#include "joint/bounded_queue.hpp"
#include <chrono>
#include <iostream>
#include <string>
#include <vector>
using namespace std::chrono_literals;
void need(bool value,const char* why){if(!value)throw std::runtime_error(why);}
template<class F>void rejects(F&& f){bool caught=false;try{f();}catch(const std::runtime_error&){caught=true;}need(caught,"Required rejection absent");}
int main(){try{
    unsigned checks=0;
    demo_v1::Queue<int> input(2);bool eof=true;
    need(!input.pop_for(1ms,eof)&&!eof,"Idle input confused with EOF");++checks;
    input.push(4);input.push(5);rejects([&]{input.push(6);});++checks;
    input.close();auto a=input.pop_for(1ms,eof);need(a&&*a==4&&!eof,"Closed queue did not drain first row");
    auto b=input.pop_for(1ms,eof);need(b&&*b==5&&!eof,"Input order/ownership differs");
    need(!input.pop_for(1ms,eof)&&eof,"Drained EOF missing");++checks;
    demo_v1::Queue<int> failed(2);failed.push(7);
    failed.fail(std::make_exception_ptr(std::runtime_error("first")));
    failed.fail(std::make_exception_ptr(std::runtime_error("second")));
    try{failed.pop_for(1ms,eof);need(false,"Queue error ignored");}catch(const std::runtime_error& e){need(std::string(e.what())=="first","First queue error lost");}
    need(failed.drain_for_evidence().front()==7,"Failed input not retained");++checks;
    DisplayFlight flight;std::vector<std::string> events;unsigned completed=0,polls=0;
    auto poll=[&]{events.push_back("poll");return ++polls>=2;};
    auto complete=[&](uint64_t id){need(id==completed,"Completion order differs");events.push_back("adopt"+std::to_string(id));++completed;};
    flight.begin(0,[&]{events.push_back("flip0");});
    rejects([&]{flight.begin(1,[&]{events.push_back("illegal_flip");});});++checks;
    events.push_back("NPU1"); // Actual main uses this gap for next process_window.
    need(!flight.service(poll,complete)&&flight.active()&&completed==0,"Premature adoption/completion");
    need(flight.service(poll,complete)&&!flight.active()&&completed==1,"Adoption not completed exactly once");
    need(events==std::vector<std::string>({"flip0","NPU1","poll","poll","adopt0"}),"NPU/adoption overlap order differs");++checks;
    need(!flight.service([]{throw std::runtime_error("Unexpected poll");return true;},complete),"Idle flight polled SDK");++checks;
    flight.begin(1,[]{});polls=0;
    while(flight.active())flight.service(poll,complete);
    need(completed==2,"Tail frame required an extra NPU frame");++checks;
    flight.begin(2,[]{});
    rejects([&]{flight.service([]()->bool{throw std::runtime_error("driver fault");},complete);});
    need(flight.active()&&completed==2,"Fault hid pending unconfirmed output");++checks;
    DisplayFlight begin_failure;
    rejects([&]{begin_failure.begin(0,[]{throw std::runtime_error("write failure");});});
    need(!begin_failure.active(),"Failed submission got a completion token");++checks;
    DisplayFlight completion_failure;completion_failure.begin(0,[]{});
    rejects([&]{completion_failure.service([]{return true;},[](uint64_t){throw std::runtime_error("handoff fault");});});
    need(completion_failure.active(),"Failed handoff erased its pending identity");++checks;
    std::cout<<"{\"passed\":true,\"checks\":"<<checks<<",\"SDK\":0,\"MMIO\":0}\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}}
