// Transport-only positive control: repeat an actual captured IDR at10fps.
// No VPU/NPU/model/HDMI. This is deliberate backpressure, not inference throughput.
#include "guarded_rtsp.hpp"
#include <atomic>
#include <chrono>
#include <fstream>
#include <iostream>
#include <thread>

namespace {
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
pose::stream::AccessUnit seed(const std::filesystem::path& fixture){
    std::ifstream input(fixture/"video.h264",std::ios::binary),index(fixture/"packets.tsv");check(bool(input)&&bool(index),"Capture seed missing");
    pose::stream::AccessUnitAssembler parser;int64_t pts;size_t size;unsigned rows=0;
    while(index>>pts>>size){check(++rows<=4&&size<=262144,"Seed bounds invalid");pose::stream::Bytes data(size);check(bool(input.read(reinterpret_cast<char*>(data.data()),size)),"Seed read failed");if(auto unit=parser.consume(data,pts)){check(unit->idr&&unit->slice.size()>=20000,"Pressure seed not expected actual IDR");return *unit;}}
    throw std::runtime_error("No initial IDR");
}
}
int main(int argc,char**argv){try{
    check(argc==4&&std::string(argv[1])=="--allow-network-control-test","Usage: --allow-network-control-test ACTUAL-CAPTURE FRESH-RESULTS");
    auto picture=seed(argv[2]);const std::filesystem::path out=argv[3];check(!std::filesystem::exists(out),"Preserve pressure evidence");std::filesystem::create_directory(out);
    pose::stream::AccessUnitChannel channel;std::atomic<bool> stopped{false};std::exception_ptr netFailure,producerFailure;unsigned produced=0;
    std::thread network([&]{try{pose::stream::GuardedRtspOptions options;options.maximumSeconds=35;pose::stream::serveGuardedAccessUnits(channel,options,out/"network");}catch(...){netFailure=std::current_exception();}stopped=true;});
    try{
        auto start=std::chrono::steady_clock::now();
        while(produced<300&&!stopped){
            std::this_thread::sleep_until(start+std::chrono::milliseconds(produced*100));if(stopped)break;
            auto unit=picture;unit.id=produced;unit.ptsUs=std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now()-start).count();channel.publish(std::move(unit));++produced;
        }
        channel.close();
    }catch(...){producerFailure=std::current_exception();channel.fail(producerFailure);}
    network.join();std::string reason;
    try{if(netFailure)std::rethrow_exception(netFailure);if(producerFailure)std::rethrow_exception(producerFailure);}catch(const std::exception&e){reason=e.what();}
    std::ofstream summary(out/"summary.json");summary<<"{\"scope\":\"network_only_repeated_actual_IDR\",\"produced\":"<<produced<<",\"AU_high_water\":"<<channel.highWater()<<",\"rejected\":"<<(!reason.empty()?"true":"false")<<",\"VPU_NPU\":false}\n";
    if(!reason.empty()){std::cerr<<"UNEXPECTED STOP: "<<reason<<'\n';return 1;}
    std::cerr<<"Normal reader control completed\n";return 0;
}catch(const std::exception&e){std::cerr<<"SETUP STOP: "<<e.what()<<'\n';return 2;}}
