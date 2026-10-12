#include "input_read_contract.hpp"
#include <stdexcept>
namespace pose::input_read {
void boundedRead(HostView v,size_t bytes,const std::function<void(char*,size_t)>& reader){
    if(!v.data||!bytes||bytes>1024*1024||v.offset>v.capacity||bytes>v.capacity-v.offset||!reader)
        throw std::runtime_error("Input read Host destination/byte contract differs");
    reader(v.data,bytes); // data already points at the tensor start; no second offset.
}
}
