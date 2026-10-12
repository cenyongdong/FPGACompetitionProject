#include "producer_schedule.hpp"
#include <iostream>
int main(){try{
    namespace s=pose::producer_schedule;
    if(s::due(1000,0)!=1000||s::due(1000,1)!=198020802||s::due(0,99)!=19603960396ULL){throw std::runtime_error("5.05Hz arithmetic differs");}
    if(s::inSlot(1000,999)||!s::inSlot(1000,1000)||!s::inSlot(1000,1000+s::period-1)||s::inSlot(1000,1000+s::period)){throw std::runtime_error("Missed slot policy differs");}
    for(auto pair:{std::pair<uint64_t,unsigned>{0,100},{std::numeric_limits<uint64_t>::max(),0}}){bool stopped=false;try{s::due(pair.first,pair.second);}catch(const std::exception&){stopped=true;}if(!stopped){throw std::runtime_error("Invalid schedule accepted");}}
    std::cout<<"Fixed100/5.05Hz/slot boundaries/overflow contracts passed.\n";return 0;
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
