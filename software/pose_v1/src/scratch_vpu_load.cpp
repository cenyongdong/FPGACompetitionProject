#include "scratch_vpu_load.hpp"
#include "vpu_resident_encoder.hpp"
#include <atomic>
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <mutex>
#include <thread>
#include <stdexcept>
namespace pose::scratch {
namespace {uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}}
struct VpuLoad::Impl {
    std::filesystem::path out;std::atomic<bool> stop{false},abort{false};std::mutex mutex;std::condition_variable cv;std::exception_ptr error;bool ready=false;std::thread worker;uint64_t first=0,last=0;unsigned packets=0;pose::video::EncodeResult result{};
    explicit Impl(const std::filesystem::path& path):out(path){if(std::filesystem::exists(out))throw std::runtime_error("Preserve VPU load evidence");std::filesystem::create_directory(out);
        worker=std::thread([this]{try{namespace v=pose::video;std::ofstream log(out/"packets.jsonl");v::ResidentOptions options;options.allowVpuStream=true;options.frameLimit=1000;
            auto produce=[&](unsigned id,uint64_t sampled)->std::optional<v::ResidentSample>{if(abort.load())throw std::runtime_error("Scratch global abort");if(stop.load())return {};
                v::OwnedFrame frame;frame.nv12.assign(v::nv12FrameBytes,128);std::fill(frame.nv12.begin(),frame.nv12.begin()+1280*720,80);frame.encodedId=id;frame.inferenceResult=false;frame.generatedNs=now();
                for(unsigned bit=0;bit<10;++bit)for(unsigned y=604;y<632;++y)for(unsigned x=44+bit*64;x<84+bit*64;++x)frame.nv12[y*1280+x]=(id&(1u<<bit))?235:16;
                return v::ResidentSample{std::move(frame),std::max(sampled,now())};};
            result=v::encodeResident(out/"encoder",options,produce,[&](v::OwnedPacket packet){last=now();log<<"{\"packet\":"<<packets++<<",\"capture_ns\":"<<last<<",\"pts_us\":"<<packet.ptsUs<<",\"bytes\":"<<packet.bytes.size()<<",\"owned\":true}\n";},[&]{std::lock_guard<std::mutex> lock(mutex);first=now();ready=true;cv.notify_all();});
        }catch(...){std::lock_guard<std::mutex> lock(mutex);error=std::current_exception();cv.notify_all();}});
    }
};
VpuLoad::VpuLoad(const std::filesystem::path& out):p_(std::make_unique<Impl>(out)){}
VpuLoad::~VpuLoad(){if(p_->worker.joinable()){p_->abort=true;p_->stop=true;p_->worker.join();}}
void VpuLoad::waitReady(){std::unique_lock<std::mutex> lock(p_->mutex);if(!p_->cv.wait_for(lock,std::chrono::seconds(5),[&]{return p_->ready||bool(p_->error);}))throw std::runtime_error("Scratch first VPU capture timeout");if(p_->error)std::rethrow_exception(p_->error);}
void VpuLoad::check(){std::lock_guard<std::mutex> lock(p_->mutex);if(p_->error)std::rethrow_exception(p_->error);}
void VpuLoad::requestStop(bool abort){p_->abort=abort;p_->stop=true;}
void VpuLoad::join(){if(p_->worker.joinable())p_->worker.join();std::ofstream f(p_->out/"summary.json");f<<"{\"first_capture_ns\":"<<p_->first<<",\"last_capture_ns\":"<<p_->last<<",\"packets\":"<<p_->packets<<",\"submitted\":"<<p_->result.submitted<<",\"returned\":"<<p_->result.returned<<",\"drained\":"<<(p_->result.drained?"true":"false")<<",\"SDK_on_encoder_thread\":false,\"joined\":true}\n";f.close();if(!f)throw std::runtime_error("VPU load summary save failed");}
}
