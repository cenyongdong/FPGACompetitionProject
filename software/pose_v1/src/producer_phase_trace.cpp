#include "producer_phase_trace.hpp"
#include "producer_schedule.hpp"
#include <chrono>
#include <exception>
#include <fstream>
#include <stdexcept>
#include <thread>
#include <vector>
#include <sys/resource.h>
#include <time.h>
namespace pose::producer_phase {
namespace {
const char* name(Phase p){
    static constexpr const char* names[]={"sleep","video_check","directory","save_input","save_identity","sdk_call","compare","save_comparison","end_check","owner_check","validate","host_allocate","host_storage","input_bytes","host_write","journal_open","journal_flush","deadline","reset","forward","output_storage","wait","output_allocate","copy","host_read","save_output","save_trace"};
    auto i=static_cast<unsigned>(p);if(i>=sizeof(names)/sizeof(names[0])){throw std::runtime_error("Unknown phase");}return names[i];
}
struct Event {Phase phase;int64_t value;unsigned invocation;bool begin,exceptional;uint64_t wall,cpu;long minor,major,voluntary,involuntary;};
}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
bool beforeDeadline(uint64_t planned,uint64_t actual){return pose::producer_schedule::inSlot(planned,actual);}
struct Trace::Impl {std::vector<Event> events;size_t capacity;unsigned invocation=0;bool failed=false;std::thread::id owner=std::this_thread::get_id();explicit Impl(size_t n):capacity(n){if(!n||n>16384){throw std::runtime_error("Phase capacity invalid");}events.reserve(n);}};
Trace::Trace(size_t n):p_(std::make_unique<Impl>(n)){}
Trace::~Trace()=default;
void Trace::check()const{if(p_->failed||p_->owner!=std::this_thread::get_id()){throw std::runtime_error("Phase trace capacity/owner failure");}}
void Trace::invocation(unsigned i){check();if(i>=100){throw std::runtime_error("Phase invocation invalid");}p_->invocation=i;}
void Trace::mark(Phase phase,int64_t value,bool begin,bool exceptional){
    check();name(phase);if(p_->events.size()==p_->capacity){p_->failed=true;throw std::runtime_error("Phase trace full");}
    timespec cpu{};rusage usage{};
    if(clock_gettime(CLOCK_THREAD_CPUTIME_ID,&cpu)||getrusage(RUSAGE_THREAD,&usage)){p_->failed=true;throw std::runtime_error("Thread resource snapshot failed");}
    p_->events.push_back({phase,value,p_->invocation,begin,exceptional,now(),static_cast<uint64_t>(cpu.tv_sec)*1000000000ULL+static_cast<uint64_t>(cpu.tv_nsec),usage.ru_minflt,usage.ru_majflt,usage.ru_nvcsw,usage.ru_nivcsw});
}
Trace::Span::Span(Trace&t,Phase p,int64_t v):trace_(t),phase_(p),value_(v),exceptions_(std::uncaught_exceptions()){trace_.mark(phase_,value_,true);}
Trace::Span::~Span()noexcept{try{trace_.mark(phase_,value_,false,std::uncaught_exceptions()>exceptions_);}catch(...){trace_.p_->failed=true;}}
void Trace::save(const std::filesystem::path&path)const{
    // Saving may follow a trace failure; preserve its bounded prefix and flag.
    if(p_->owner!=std::this_thread::get_id()||std::filesystem::exists(path)){throw std::runtime_error("Phase save owner/preservation failure");}
    std::ofstream f(path);
    for(const auto&e:p_->events){f<<"{\"phase\":\""<<name(e.phase)<<"\",\"value\":"<<e.value<<",\"invocation\":"<<e.invocation<<",\"edge\":\""<<(e.begin?"begin":"end")<<"\",\"exceptional\":"<<(e.exceptional?"true":"false")<<",\"wall_ns\":"<<e.wall<<",\"thread_cpu_ns\":"<<e.cpu<<",\"minor_faults\":"<<e.minor<<",\"major_faults\":"<<e.major<<",\"voluntary_switches\":"<<e.voluntary<<",\"involuntary_switches\":"<<e.involuntary<<",\"trace_failed\":"<<(p_->failed?"true":"false")<<"}\n";}
    f.close();if(!f){throw std::runtime_error("Phase save failed");}
}
}
