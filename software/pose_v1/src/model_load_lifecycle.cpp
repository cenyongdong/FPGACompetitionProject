#include "model_load_lifecycle.hpp"
#include <stdexcept>
namespace pose::load_lifecycle {
namespace {void need(bool b,const char*m){if(!b){throw std::runtime_error(m);}}}
void Control::owner()const{need(owner_==std::this_thread::get_id(),"Load lifecycle owner changed");}
Control::Control(bool enabled,Hooks hooks):enabled_(enabled),hooks_(std::move(hooks)){
    if(enabled_){need(hooks_.start&&hooks_.waitReady&&hooks_.check&&hooks_.join&&hooks_.requestStop,"Load lifecycle hooks absent");}
}
void Control::start(){owner();need(state_==State::idle,"Load start repeated");state_=State::attempted;if(enabled_){hooks_.start();hooks_.waitReady();hooks_.check();}state_=State::ready;}
void Control::check()const{owner();need(state_==State::ready,"Load check outside ready state");if(enabled_){hooks_.check();}}
void Control::finish(std::exception_ptr&failure){
    owner();need(state_!=State::joined,"Load finish repeated");
    if(enabled_&&state_!=State::idle){
        try{hooks_.requestStop(bool(failure));}catch(...){if(!failure){failure=std::current_exception();}}
        try{hooks_.join();}catch(...){if(!failure){failure=std::current_exception();}}
        try{hooks_.check();}catch(...){if(!failure){failure=std::current_exception();}}
    }state_=State::joined;
}
bool Control::joined()const{owner();return state_==State::joined;}
}
