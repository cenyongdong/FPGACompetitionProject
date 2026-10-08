// Network adapter gate only. Replay captured packets through a producer thread;
// no VPU/Engine is opened. Actual recorded capture PTS, no nominal timestamp.
#include "online_rtsp.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <sstream>
#include <thread>
#include <atomic>

namespace {
void check(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct Packet{int64_t pts;pose::stream::Bytes bytes;};
std::vector<Packet> load(const std::filesystem::path& path){
    check(std::filesystem::file_size(path/"video.h264")<16*1024*1024,"Capture blob too large");
    std::ifstream video(path/"video.h264",std::ios::binary),index(path/"packets.tsv");check(bool(video)&&bool(index),"Fixture open failed");
    std::vector<Packet> packets;std::string row;size_t total=0;int64_t last=-1;
    while(std::getline(index,row)){
        std::istringstream fields(row);int64_t pts;size_t n;std::string extra;check(bool(fields>>pts>>n)&&!(fields>>extra),"Packet index invalid");
        check((pts>=last||(n==0&&pts==0))&&pts>=0&&pts<=90000000&&n<=262144&&packets.size()<1002,"Packet limits invalid");if(n)last=pts;
        Packet packet{pts,pose::stream::Bytes(n)};check(n==0||bool(video.read(reinterpret_cast<char*>(packet.bytes.data()),n)),"Capture index incomplete");total+=n;packets.push_back(std::move(packet));
    }
    check(total==std::filesystem::file_size(path/"video.h264")&&!packets.empty(),"Capture coverage invalid");return packets;
}
}
int main(int argc,char**argv){try{
    check(argc==4&&std::string(argv[1])=="--allow-network-replay","Usage: --allow-network-replay CAPTURE-PACKAGE FRESH-RESULTS");
    auto packets=load(argv[2]);pose::stream::AccessUnitChannel channel;std::atomic<bool> cancel{false};std::exception_ptr networkFailure;
    std::thread network([&]{try{pose::stream::serveOwnedAccessUnits(channel,{},argv[3]);}catch(...){networkFailure=std::current_exception();cancel=true;}});
    std::exception_ptr producerFailure;
    try{
        pose::stream::AccessUnitAssembler assembler;auto begin=std::chrono::steady_clock::now();
        for(const auto& packet:packets){
            const auto due=begin+std::chrono::microseconds(packet.pts);
            while(std::chrono::steady_clock::now()<due&&!cancel)std::this_thread::sleep_for(std::chrono::milliseconds(1));
            check(!cancel,"Network failed before producer completion");
            if(auto unit=assembler.consume(packet.bytes,packet.pts))channel.publish(std::move(*unit));
        }
        check(assembler.pictures()>0,"No owned access units");channel.close();
    }catch(...){producerFailure=std::current_exception();channel.fail(producerFailure);}
    network.join();if(networkFailure)std::rethrow_exception(networkFailure);if(producerFailure)std::rethrow_exception(producerFailure);
    std::cout<<"Completed owned AU adapter gate; queue highwater="<<channel.highWater()<<"; VPU/NPU not opened"<<std::endl;return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
