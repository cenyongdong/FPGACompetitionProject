#include "producer_phase_trace.hpp"
#include "producer_schedule.hpp"
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <thread>
namespace {void need(bool x){if(!x){throw std::runtime_error("Phase contract failed");}}}
int main(int argc,char**argv){try{
    namespace pp=pose::producer_phase;need(argc==2);std::filesystem::path out=argv[1];need(!std::filesystem::exists(out));std::filesystem::create_directory(out);
    const uint64_t planned=1000ULL;const auto period=pose::producer_schedule::period;
    need(!pp::beforeDeadline(planned,planned-1));need(pp::beforeDeadline(planned,planned));need(pp::beforeDeadline(planned,planned+period-1));need(!pp::beforeDeadline(planned,planned+period));
    unsigned forwards=0;for(auto actual:{planned+period,planned+period+1}){if(pp::beforeDeadline(planned,actual)){++forwards;}}need(forwards==0);
    pp::Trace trace(8);trace.invocation(7);int calls=0;auto value=trace.run(pp::Phase::HostWrite,486,[&]{++calls;return 42;});need(value==42&&calls==1);
    try{trace.run(pp::Phase::SaveInput,478,[]{throw std::runtime_error("original failure");});}catch(const std::runtime_error&e){need(std::string(e.what())=="original failure");}
    bool rejected=false;std::thread wrong([&]{try{trace.check();}catch(...){rejected=true;}});wrong.join();need(rejected);trace.check();trace.save(out/"normal.jsonl");
    pp::Trace full(1);try{full.run(pp::Phase::Compare,0,[]{});}catch(...){throw std::runtime_error("Destructor must not mask errors");}rejected=false;try{full.check();}catch(...){rejected=true;}need(rejected);full.save(out/"full.jsonl");
    rejected=false;try{trace.save(out/"normal.jsonl");}catch(...){rejected=true;}need(rejected);
    std::ifstream f(out/"normal.jsonl");std::string line;int lines=0;bool exceptional=false;while(std::getline(f,line)){++lines;exceptional|=line.find("\"exceptional\":true")!=std::string::npos;}need(lines==4&&exceptional);
    std::cout<<"Phase ownership/capacity/exception/return and absolute deadline no-forward contracts passed\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
