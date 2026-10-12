#include "model_only_run.hpp"
#include <limits>
#include <stdexcept>
namespace pose::model_only {
namespace {void need(bool ok,const char*why){if(!ok){throw std::runtime_error(why);}}}
void Run::owner()const{need(owner_==std::this_thread::get_id(),"Model-only owner changed");}
Run::Run(std::vector<pose::validation::FixtureWindow>cases,size_t limit):cases_(std::move(cases)),limit_(limit){
    need((limit==4&&cases_.size()==4)||(limit==103&&cases_.size()==27),"Model-only finite source contract differs");returned_.reserve(limit);
}
void Run::step(const Process&process,const SaveThenVerify&gate){
    owner();need(!stopped_&&attempts_<limit_,"Model-only stopped or source exhausted");need(bool(process)&&bool(gate),"Model-only callbacks absent");
    const size_t i=attempts_++;const auto&fixture=cases_[i%cases_.size()];
    current_=Attempt{i,fixture.window.frame_id,fixture.name,fixture.window};current_->window.frame_id=100000+i;
    try{
        auto result=process(current_->window);
        returned_.push_back(Returned{*current_,std::move(result),false});
        gate(fixture,returned_.back());returned_.back().verified=true;
    }catch(...){stopped_=true;throw;}
}
const std::vector<Returned>&Run::returned()const{owner();return returned_;}
const std::optional<Attempt>&Run::current()const{owner();return current_;}
size_t Run::attempts()const{owner();return attempts_;}
bool Run::stopped()const{owner();return stopped_;}
uint64_t scheduledStart(uint64_t epoch,size_t index,uint64_t previous,uint64_t period){
    need(epoch>0&&period>0&&index<103,"Invalid finite schedule");
    const auto maximum=std::numeric_limits<uint64_t>::max();need(period<=(maximum-epoch)/(index?index:1),"Schedule overflow");
    auto result=epoch+index*period;
    if(index){need(previous>=epoch&&previous<=maximum-period,"Previous schedule invalid");if(previous+period>result){result=previous+period;}}
    return result;
}
}
