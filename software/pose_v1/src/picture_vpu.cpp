#include "picture_vpu.hpp"
#include "picture_source.hpp"
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <mutex>
#include <thread>
#include <stdexcept>
namespace pose::picture {
namespace {uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}}
struct Vpu::Impl {
    std::filesystem::path out;Source source;std::mutex mutex;std::condition_variable cv;std::exception_ptr error;bool ready=false;std::thread worker;
    uint64_t first=0,last=0;unsigned packets=0;pose::video::EncodeResult result{};
    Impl(const std::filesystem::path& p,pose::video::OwnedFrame warm):out(p),source(std::move(warm)){
        if(std::filesystem::exists(out)){throw std::runtime_error("Preserve picture VPU evidence");}std::filesystem::create_directory(out);
        worker=std::thread([this]{try{
            namespace v=pose::video;std::ofstream samples(out/"samples.jsonl"),log(out/"packets.jsonl");if(!samples||!log){throw std::runtime_error("Picture trace open failed");}
            v::ResidentOptions options;options.allowVpuStream=true;options.frameLimit=1000;
            result=v::encodeResident(out/"encoder",options,[&](unsigned id,uint64_t sampled){
                auto candidate=source.sample(id,sampled);if(candidate){const auto& f=candidate->frame;
                    samples<<"{\"encoded_id\":"<<id<<",\"sample_ns\":"<<candidate->sampledNs<<",\"source_frame_id\":"<<f.sourceFrame<<",\"invocation\":"<<f.invocation<<",\"generated_ns\":"<<f.generatedNs<<",\"inference_result\":"<<(f.inferenceResult?"true":"false")<<",\"repeated_source\":"<<(f.repeatedSource?"true":"false")<<",\"marked_NV12_fnv1a64\":\""<<frameHash(f.nv12)<<"\"}\n";
                    if(!samples){throw std::runtime_error("Picture sample trace failed");}}
                return candidate;
            },[&](v::OwnedPacket packet){last=now();log<<"{\"packet\":"<<packets++<<",\"capture_ns\":"<<last<<",\"pts_us\":"<<packet.ptsUs<<",\"bytes\":"<<packet.bytes.size()<<",\"owned\":true}\n";if(!log){throw std::runtime_error("Picture packet trace failed");}},[&]{std::lock_guard<std::mutex> lock(mutex);first=now();ready=true;cv.notify_all();});
            samples.close();log.close();if(!samples||!log){throw std::runtime_error("Picture trace close failed");}
        }catch(...){std::lock_guard<std::mutex> lock(mutex);error=std::current_exception();source.fail(error);cv.notify_all();}});
    }
};
Vpu::Vpu(const std::filesystem::path& p,pose::video::OwnedFrame warm):p_(std::make_unique<Impl>(p,std::move(warm))){}
Vpu::~Vpu(){if(p_->worker.joinable()){p_->source.fail(std::make_exception_ptr(std::runtime_error("Picture cleanup abort")));p_->worker.join();}}
void Vpu::waitReady(){std::unique_lock<std::mutex> lock(p_->mutex);if(!p_->cv.wait_for(lock,std::chrono::seconds(5),[&]{return p_->ready||bool(p_->error);})){throw std::runtime_error("Picture first capture timeout");}if(p_->error){std::rethrow_exception(p_->error);}}
void Vpu::check(){std::lock_guard<std::mutex> lock(p_->mutex);if(p_->error){std::rethrow_exception(p_->error);}p_->source.check();}
void Vpu::publish(pose::video::OwnedFrame f){check();p_->source.publish(std::move(f));}
void Vpu::requestStop(bool abort){if(abort){p_->source.fail(std::make_exception_ptr(std::runtime_error("Picture global abort")));}else{p_->source.stop();}}
void Vpu::join(){if(p_->worker.joinable()){p_->worker.join();}const auto q=p_->source.stats();std::ofstream f(p_->out/"summary.json");
    f<<"{\"first_capture_ns\":"<<p_->first<<",\"last_capture_ns\":"<<p_->last<<",\"packets\":"<<p_->packets<<",\"submitted\":"<<p_->result.submitted<<",\"returned\":"<<p_->result.returned<<",\"drained\":"<<(p_->result.drained?"true":"false")<<",\"SDK_on_encoder_thread\":false,\"joined\":true,\"queue_capacity\":2,\"published\":"<<q.published<<",\"consumed\":"<<q.consumed<<",\"overwritten\":"<<q.overwritten<<",\"coalesced\":"<<q.coalesced<<",\"high_water\":"<<q.highWater<<"}\n";
    f.close();if(!f){throw std::runtime_error("Picture VPU summary failed");}
}
}
