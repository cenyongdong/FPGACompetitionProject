#include "demo_video.hpp"
#include "display_queue.hpp"
#include "resident_frame_queue.hpp"
#include "skeleton_render.hpp"
#include "vpu_resident_encoder.hpp"
#include "guarded_rtsp.hpp"
#include "video_frame_marker.hpp"
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <fstream>
#include <mutex>
#include <thread>

namespace wifi_demo {
namespace {
uint64_t now() { return std::chrono::duration_cast<std::chrono::nanoseconds>(
    std::chrono::steady_clock::now().time_since_epoch()).count(); }
void need(bool v,const char* why) {if(!v) throw std::runtime_error(why);}
}
struct Video::Impl {
    pose::display::Process& display;
    pose::display::Queue poses;
    pose::video::ResidentFrameQueue frames;
    pose::stream::AccessUnitChannel channel;
    std::thread renderer, encoder, network;
    std::mutex mutex; std::condition_variable cv;
    std::exception_ptr error;
    std::atomic<bool> stopping{false}, done{false};
    std::atomic<uint64_t> initBegin{0}, initEnd{0}, productionEnd{0};
    bool capture=false, joined=false;
    std::filesystem::path root;
    std::ofstream samples, packets, rendering;
    pose::video::EncodeResult encoded{};
    explicit Impl(pose::display::Process& d,const std::filesystem::path& out,unsigned port)
        : display(d),root(out) {
        need(std::filesystem::create_directory(root),"Fresh video directory required");
        samples.open(root/"samples.jsonl"); packets.open(root/"packets.jsonl"); rendering.open(root/"display.jsonl");
        need(bool(samples)&&bool(packets)&&bool(rendering),"Video logs open failed");
        auto rgb=pose_v1::render::draw({}, {},0,pose_v1::render::Status::NoInput);
        pose::video::OwnedFrame warm;warm.nv12=pose_v1::render::yuv420sp(rgb.rgb,1280,720,false);
        warm.generatedNs=now();warm.inferenceResult=false;
        try {
            network=std::thread([this,port]{try {
                pose::stream::GuardedRtspOptions cfg;cfg.port=port;cfg.maximumSeconds=175;
                pose::stream::serveGuardedAccessUnits(channel,cfg,root/"network");
            } catch(...) {fail(std::current_exception());}});
            renderer=std::thread([this]{try {
                while(auto p=poses.next()) {
                    auto image=display.render(*p,[this]{return stopping.load();});
                    pose::video::OwnedFrame f;f.nv12=std::move(image.nv12);f.sourceFrame=image.frame;
                    f.invocation=image.invocation;f.generatedNs=image.convertEnd;frames.publish(std::move(f));
                    rendering<<"{\"frame\":"<<image.frame<<",\"invocation\":"<<image.invocation
                        <<",\"render_begin_ns\":"<<image.renderBegin<<",\"convert_end_ns\":"<<image.convertEnd<<"}\n";
                }
                display.finish();
            } catch(...) {fail(std::current_exception());}});
            encoder=std::thread([this,warm=std::move(warm)]{try {
                auto latest=std::make_shared<const pose::video::OwnedFrame>(warm);
                uint64_t previous=0;bool previousReal=false;pose::stream::AccessUnitAssembler assembler;
                auto produce=[&](unsigned id,uint64_t)->std::optional<pose::video::ResidentSample> {
                    frames.check();need(!stopping,"Video aborted");
                    const auto stamp=now(),begin=initBegin.load(),end=initEnd.load(),finished=productionEnd.load();
                    need(!begin||end||stamp-begin<60000000000ULL,"Engine initialization exceeds60s");
                    if(done&&finished&&stamp-finished>=2000000000ULL) {frames.stop();return {};}
                    if(auto p=frames.popLatest()) latest=std::move(p);
                    auto f=*latest;f.encodedId=id;f.repeatedSource=f.inferenceResult&&previousReal&&previous==f.invocation;
                    previous=f.invocation;previousReal=f.inferenceResult;
                    pose::validation::markEncodedFrame(f.nv12,id);
                    const auto sampled=now();samples<<"{\"encoded_id\":"<<id<<",\"sample_ns\":"<<sampled
                        <<",\"source_frame\":"<<f.sourceFrame<<",\"invocation\":"<<f.invocation
                        <<",\"inference_result\":"<<(f.inferenceResult?"true":"false")
                        <<",\"repeated\":"<<(f.repeatedSource?"true":"false")<<"}\n";
                    return pose::video::ResidentSample{std::move(f),sampled};
                };
                auto packet=[&](pose::video::OwnedPacket p) {
                    packets<<"{\"pts_us\":"<<p.ptsUs<<",\"bytes\":"<<p.bytes.size()<<",\"flags\":"<<p.flags<<"}\n";
                    if(auto au=assembler.consume(p.bytes,p.ptsUs)) channel.publish(std::move(*au));
                };
                pose::video::ResidentOptions cfg;cfg.allowVpuStream=true;
                encoded=pose::video::encodeResident(root/"encoder",cfg,produce,packet,[this]{
                    {std::lock_guard<std::mutex> lock(mutex);capture=true;}cv.notify_all();});
                channel.close();
            } catch(...) {fail(std::current_exception());}});
        } catch(...) {fail(std::current_exception());join();throw;}
    }
    void fail(std::exception_ptr e) {
        {std::lock_guard<std::mutex> lock(mutex);if(!error)error=e;}
        stopping=true;poses.fail(e);frames.fail(e);try {channel.fail(e);}catch(...){}cv.notify_all();
    }
    void check() {std::lock_guard<std::mutex> lock(mutex);if(error)std::rethrow_exception(error);}
    void join() {
        if(joined)return;
        poses.close();if(renderer.joinable())renderer.join();productionEnd=now();done=true;
        if(encoder.joinable())encoder.join();
        if(network.joinable())network.join();
        joined=true;
        samples.close();packets.close();rendering.close();
        const auto a=poses.stats();const auto b=frames.stats();
        std::ofstream f(root/"summary.json");f<<"{\"pose_published\":"<<a.published<<",\"pose_adopted\":"<<a.adopted
            <<",\"pose_overwritten\":"<<a.overwritten<<",\"pose_coalesced\":"<<a.coalesced
            <<",\"frame_adopted\":"<<b.consumed<<",\"frame_overwritten\":"<<b.overwritten
            <<",\"frame_coalesced\":"<<b.coalesced<<",\"encoded\":"<<encoded.submitted
            <<",\"returned\":"<<encoded.returned<<",\"drained\":"<<(encoded.drained?"true":"false")
            <<",\"workers_joined\":true,\"NoInput_and_repeated_not_new_pose_throughput\":true}\n";
        if(!f) {try {throw std::runtime_error("Video summary write failed");}catch(...) {fail(std::current_exception());}}
    }
};
Video::Video(pose::display::Process& p,const std::filesystem::path& o,unsigned port):p_(std::make_unique<Impl>(p,o,port)){}
Video::~Video(){if(p_&&!p_->joined){try {p_->join();}catch(...) {}}}
void Video::waitCapture(){std::unique_lock<std::mutex> l(p_->mutex);need(p_->cv.wait_for(l,std::chrono::seconds(5),[&]{return p_->capture||p_->error;}),"VPU first capture exceeds5s");if(p_->error)std::rethrow_exception(p_->error);}
void Video::beginInitialization(){p_->initBegin=now();}
void Video::initialized(){p_->initEnd=now();p_->check();}
void Video::publish(pose::display::Pose p){p_->check();p_->poses.publish(std::move(p));}
void Video::check(){p_->check();}
void Video::abort(std::exception_ptr e){p_->fail(e);}
void Video::finish(){p_->join();p_->check();}
}
