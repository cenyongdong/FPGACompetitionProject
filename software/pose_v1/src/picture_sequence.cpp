#include "resident_sequence.hpp"
#include <stdexcept>
namespace pose::resident_sequence {
namespace {
constexpr Stage stages[]={{"three",0,4,500000000},{"load-103",4,103,500000000}};
void need(bool ok,const char* why){if(!ok){throw std::runtime_error(why);}}
}
void Sequence::owner()const{need(owner_==std::this_thread::get_id(),"Resident sequence owner changed");}
Stage Sequence::begin(){owner();need(!failed_&&!active_&&phase_<2,"Resident stage cannot start");active_=true;completed_=0;return stages[phase_];}
size_t Sequence::invocation()const{owner();need(!failed_&&active_&&completed_<stages[phase_].count,"Resident call unavailable");return stages[phase_].offset+completed_;}
void Sequence::completeCall(){(void)invocation();++completed_;}
void Sequence::advance(){owner();need(!failed_&&active_&&completed_==stages[phase_].count,"Resident stage incomplete");active_=false;++phase_;}
void Sequence::stop(){owner();failed_=true;}
bool Sequence::done()const{owner();return !failed_&&!active_&&phase_==2;}
}
