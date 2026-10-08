#include "access_unit_channel.hpp"
#include <unistd.h>
#include <fcntl.h>
#include <cerrno>
#include <algorithm>
#include <stdexcept>

namespace pose::stream {
AccessUnitChannel::AccessUnitChannel(){
    if(pipe2(pipe_,O_NONBLOCK|O_CLOEXEC)!=0)throw std::runtime_error("AU notification pipe failed");
}
AccessUnitChannel::~AccessUnitChannel(){for(auto fd:pipe_)if(fd>=0)::close(fd);}
void AccessUnitChannel::notify(){
    uint8_t byte=1;ssize_t result;do{result=::write(pipe_[1],&byte,1);}while(result<0&&errno==EINTR);
    if(result!=1&&!(result<0&&errno==EAGAIN))throw std::runtime_error("AU notification failed");
}
void AccessUnitChannel::publish(AccessUnit unit){
    std::lock_guard<std::mutex> lock(mutex_);if(failure_)std::rethrow_exception(failure_);
    if(closed_)throw std::runtime_error("AU publish after close");
    if(units_.size()==capacity)throw std::runtime_error("AU backpressure capacity exceeded");
    if(unit.slice.empty()||unit.slice.size()>262144||unit.sps.empty()||unit.pps.empty()||unit.sps.size()>4096||unit.pps.size()>4096)
        throw std::runtime_error("AU channel payload invalid");
    const bool wake=units_.empty();units_.push_back(std::move(unit));highWater_=std::max(highWater_,units_.size());if(wake)notify();
}
void AccessUnitChannel::close(){std::lock_guard<std::mutex> lock(mutex_);closed_=true;notify();}
void AccessUnitChannel::fail(std::exception_ptr e){std::lock_guard<std::mutex> lock(mutex_);failure_=e;closed_=true;notify();}
AccessUnitChannel::Batch AccessUnitChannel::take(){
    uint8_t bytes[64];ssize_t result;do{result=::read(pipe_[0],bytes,sizeof(bytes));}while(result>0||(result<0&&errno==EINTR));
    if(result<0&&errno!=EAGAIN)throw std::runtime_error("AU notification read failed");
    std::lock_guard<std::mutex> lock(mutex_);if(failure_)std::rethrow_exception(failure_);
    Batch batch;batch.units.swap(units_);batch.closed=closed_;return batch;
}
size_t AccessUnitChannel::highWater()const{std::lock_guard<std::mutex> lock(mutex_);return highWater_;}
}
