#include "access_unit_channel.hpp"
#include <poll.h>
#include <atomic>
#include <thread>
#include <iostream>
#include <functional>

namespace {
using namespace pose::stream;
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
unsigned rejected=0;
void reject(std::function<void()> work){bool caught=false;try{work();}catch(const std::exception&){caught=true;}check(caught,"Expected rejection missing");++rejected;}
Bytes parameters(){return {0,0,0,1,0x67,0x42,0,30,0,0,0,1,0x68,0xce,0x38,0x80};}
Bytes picture(bool idr){return {0,0,1,uint8_t(idr?0x65:0x41),0x80,0x21};}
AccessUnit sample(uint64_t id){return {id,int64_t(id*100000),{0x67,0x42,0,30},{0x68,0xce,0x38,0x80},{0x65,0x80,0x21},true};}
}
int main(){try{
    AccessUnitAssembler parser;auto params=parameters();check(!parser.consume(params,1),"Parameters produced picture");auto bytes=picture(true);
    auto first=parser.consume(bytes,1);check(first&&first->id==0&&first->ptsUs==1&&first->idr,"Initial IDR failed");bytes[4]=0;params[4]=0;
    check(first->slice[1]==0x80&&first->sps[0]==0x67,"Parser retained borrowed input");
    check(parser.consume(picture(false),137009)->id==1,"Irregular PTS rejected");
    reject([&]{parser.consume(picture(false),137009);});reject([&]{parser.consume({0,1},200000);});
    reject([&]{parser.consume({0,0,1},200000);});reject([&]{parser.consume({0,0,1,0x81,0x80},200000);});
    reject([&]{parser.consume({0,0,1,6,0x80},200000);});reject([&]{parser.consume({0,0,1,0x41,0x40},200000);});
    auto two=picture(false);auto more=picture(false);two.insert(two.end(),more.begin(),more.end());reject([&]{parser.consume(two,200000);});
    auto changed=parameters();changed[5]=0x43;reject([&]{parser.consume(changed,200000);});
    reject([&]{parser.consume(Bytes(262145,0),200000);});reject([&]{parser.consume({},-1);});
    reject([&]{AccessUnitAssembler missing;missing.consume(picture(true),0);});
    reject([&]{AccessUnitAssembler missing;missing.consume(parameters(),0);missing.consume(picture(false),0);});
    check(parser.pictures()==2,"Rejected capture changed state");
    AccessUnitChannel bounded;for(unsigned i=0;i<8;++i)bounded.publish(sample(i));reject([&]{bounded.publish(sample(8));});
    auto batch=bounded.take();check(batch.units.size()==8&&bounded.highWater()==8,"Bounded channel lost units");
    for(unsigned i=0;i<8;++i)check(batch.units[i].id==i,"Channel reordered P chain");
    bounded.close();check(bounded.take().closed,"Close notification missing");reject([&]{bounded.publish(sample(9));});
    AccessUnitChannel failing;failing.fail(std::make_exception_ptr(std::runtime_error("synthetic")));reject([&]{failing.take();});reject([&]{failing.publish(sample(0));});
    AccessUnitChannel invalid;auto bad=sample(0);bad.slice.clear();reject([&]{invalid.publish(bad);});
    // Saturation is already tested above; this exercises concurrent wakeup/drain
    // races without relying on scheduler-dependent overflow/retry behavior.
    AccessUnitChannel channel;std::atomic<uint64_t> consumed{0};std::atomic<bool> cancel{false};std::exception_ptr producerFailure;
    std::thread producer([&]{try{for(uint64_t i=0;i<2000&&!cancel;++i){while(consumed.load()!=i&&!cancel)std::this_thread::yield();if(!cancel)channel.publish(sample(i));}while(consumed.load()!=2000&&!cancel)std::this_thread::yield();channel.close();}catch(...){producerFailure=std::current_exception();channel.fail(producerFailure);}});
    uint64_t next=0;bool closed=false;
    try{while(!closed){pollfd fd{channel.notificationFd(),POLLIN,0};check(poll(&fd,1,2000)==1,"Notification lost");auto got=channel.take();for(const auto& unit:got.units){check(unit.id==next++,"Concurrent AU reordered");consumed=next;}closed=got.closed;}}
    catch(...){cancel=true;producer.join();throw;}
    producer.join();if(producerFailure)std::rethrow_exception(producerFailure);check(next==2000,"Concurrent coverage missing");
    std::cout<<"{\"status\":\"passed\",\"rejections\":"<<rejected<<",\"threaded_units\":2000,\"capacity\":8,\"no_device\":true}"<<std::endl;return 0;
}catch(const std::exception& e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
