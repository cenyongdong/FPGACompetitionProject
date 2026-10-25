#include "input_read_sdk.hpp"
#include <icraft-xrt/dev/zg330_device.h>
#include <icraft-xrt/dev/host_device.h>
#include <icraft-xrt/core/tensor.h>
#include <icraft-xir/core/data.h>
#include <array>
#include <chrono>
#include <cstring>
#include <deque>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <thread>
#include <vector>
#include <stdexcept>
namespace xrt=icraft::xrt; namespace xir=icraft::xir;
using Clock=std::chrono::steady_clock;
uint64_t ns(){return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();}
void need(bool v,const char* why){if(!v)throw std::runtime_error(why);}
void blob(const std::filesystem::path& p,const char* data,size_t n){
    std::ofstream f(p,std::ios::binary);f.write(data,n);f.close();need(bool(f),"Static evidence save failed");
}
int main(int argc,char** argv){
    if(argc!=3)return 2;
    const std::filesystem::path root=argv[1];const auto pairs=std::stoul(argv[2]);
    need(pairs>0&&pairs<=7200,"Static pair limit");
    need(!std::filesystem::exists(root),"Preserve static evidence");std::filesystem::create_directory(root);
    const auto start=ns();size_t completed=0,reads=0;uint64_t maxRead=0;std::deque<std::string> timeline;
    std::array<std::vector<float>,2> expected;
    std::array<xrt::Tensor,2> source,host;
    bool readReturned=false;size_t current=0;std::string error;int result=0;
    try{
        auto d=xrt::Device::Open("axi://zg330aiu?npu=0x40000000&dma=0x80000000");d.setWaitTime(10000);
        const auto version=d.version();
        need(version.at("device")=="25122301"&&version.at("icore")=="FMSHZGV3TECH-AID - 24160628","Static device identity differs");
        auto region=d.getMemRegion("plddr");
        need(std::string(region->typeKey())=="AXIZG330AIPLDDRMemRegionNode","Unexpected static source region");
        std::ofstream identities(root/"storage.json");identities<<"[";
        for(size_t s=0;s<2;++s){
            auto type=xir::TensorType(xir::FloatType::FP32(),{1,int64_t(s?100:180),42},xir::Layout("**C"));
            expected[s].resize(s?4200:7560);
            for(size_t i=0;i<expected[s].size();++i)expected[s][i]=s?float((i/42)%180):float(i%4096)/32.0f+0.015625f;
            source[s]=xrt::Tensor(type).mallocOn(region);
            need(source[s].data().ptype()!=xrt::PtrType::CPTR,"Static source must be device address");
            source[s].write(0,reinterpret_cast<char*>(expected[s].data()),expected[s].size()*4);
            source[s].setReady(true); // Immutable Host-written source; no NPU producer.
            blob(root/("expected"+std::to_string(s)+".f32"),reinterpret_cast<const char*>(expected[s].data()),expected[s].size()*4);
            if(s)identities<<',';
            identities<<"{\"slot\":"<<s<<",\"address\":"<<source[s].data().addr()<<",\"offset\":"<<source[s].offset()<<",\"capacity\":"<<source[s].chunk()->byte_size<<",\"bytes\":"<<type.bytes()<<"}";
        }
        identities<<"]\n";identities.close();need(bool(identities),"Static identity save failed");
        const auto pace=Clock::now();
        // Pair zero is initial validation. Any failure exits the entire batch.
        for(size_t pair=0;pair<pairs;++pair){
            std::this_thread::sleep_until(pace+std::chrono::nanoseconds(pair*1000000000ULL/30));
            for(size_t s=0;s<2;++s){
                current=s;readReturned=false;
                const auto begin=ns();need(source[s].waitForReady(std::chrono::milliseconds(10000)),"Static wait failed");
                host[s]=xrt::Tensor(source[s].dtype()).mallocOn(xrt::HostDevice::MemRegion());
                const auto copy=ns();pose::input_read::intoHost(source[s],host[s]);readReturned=true;const auto end=ns();
                // Own first bytes before comparison; never reuse a late value.
                std::vector<char> original(expected[s].size()*4);std::memcpy(original.data(),host[s].data().cptr(),original.size());
                maxRead=std::max(maxRead,end-copy);++reads;
                std::ostringstream row;row<<"{\"pair\":"<<pair<<",\"slot\":"<<s<<",\"begin_ns\":"<<begin<<",\"copy_begin_ns\":"<<copy<<",\"copy_end_ns\":"<<end<<",\"Host_CPTR\":"<<reinterpret_cast<uintptr_t>(host[s].data().cptr())<<"}";
                if(timeline.size()==256)timeline.pop_front();timeline.push_back(row.str());
                if(std::memcmp(original.data(),expected[s].data(),original.size())){
                    blob(root/"first-original.bin",original.data(),original.size());
                    blob(root/"first-shadow.bin",host[s].data().cptr(),original.size());
                    // Only a normally returned content mismatch permits two evidence reads.
                    for(size_t round=0;round<2;++round){
                        std::vector<char> late(original.size());
                        source[s].read(late.data(),0,late.size());
                        blob(root/("late"+std::to_string(round)+".bin"),late.data(),late.size());
                    }
                    throw std::runtime_error("Static first read content mismatch at pair "+std::to_string(pair)+" slot "+std::to_string(s));
                }
            }
            ++completed;
            if(completed%300==0){std::ofstream p(root/"progress.json");p<<"{\"completed_pairs\":"<<completed<<",\"elapsed_seconds\":"<<double(ns()-start)/1e9<<"}\n";}
        }
    }catch(const std::exception& e){error=e.what();result=1;}
    std::ofstream log(root/"timeline.jsonl");for(const auto& r:timeline)log<<r<<'\n';log.close();
    std::ofstream summary(root/"summary.json");summary<<std::setprecision(17)<<"{\"native_exit\":"<<result<<",\"target_pairs\":"<<pairs<<",\"completed_pairs\":"<<completed<<",\"reads\":"<<reads<<",\"current_slot\":"<<current<<",\"last_read_returned\":"<<(readReturned?"true":"false")<<",\"max_read_ms\":"<<double(maxRead)/1e6<<",\"elapsed_seconds\":"<<double(ns()-start)/1e9<<",\"NPU_running\":false,\"model_loaded\":false,\"error\":"<<std::quoted(error)<<"}\n";
    summary.close();need(bool(summary)&&bool(log),"Static final evidence save failed");
    std::cout<<"STATIC_COMPLETE pairs="<<completed<<" reads="<<reads<<" exit="<<result<<std::endl;
    return result;
}
