// Host-only adapter for the frozen CPU suite. It is not a production dependency.
#include "pipeline_fixture_source.hpp"
#include "lazy_runtime_validation.hpp"
#include "resident_frame_queue.hpp"

namespace pose::validation {
int validatedHostGate(const std::filesystem::path& package,const std::filesystem::path& output){
    namespace detail=pose_v1::runtime_detail;
    pose::video::ResidentFrameQueue queue;
    auto frame=[](uint64_t id){pose::video::OwnedFrame f;f.nv12.resize(pose::video::nv12FrameBytes,uint8_t(id));f.generatedNs=id;f.invocation=id;return f;};
    queue.publish(frame(1));queue.publish(frame(2));queue.publish(frame(3));auto latest=queue.popLatest();
    auto stats=queue.stats();detail::need(latest&&latest->invocation==3&&stats.overwritten==1&&stats.coalesced==1&&stats.highWater==2,"Frame queue contract failed");
    auto duplicate=*latest;duplicate.nv12[0]=0;detail::need(latest->nv12[0]==3,"Immutable frame ownership failed");queue.stop();
    bool refused=false;try{queue.publish(frame(4));}catch(const std::exception&){refused=true;}detail::need(refused,"Publish after stop accepted");
    auto trace=detail::file(output/"bridge.jsonl");detail::bridge::configure(&trace,false);
    std::vector<std::string> args={"live_host","--graph",(package/"graph/piw24_ZG.json").string(),"--fixtures",(package/"fixtures").string(),"--output",(output/"host").string()};
    std::vector<char*> argv;for(auto& arg:args)argv.push_back(arg.data());
    detail::need(::mixed_host_check(argv.size(),argv.data())==0,"Host107 failed");
    detail::write(output/"queue-contracts.json","{\"capacity\":2,\"overwrite_oldest\":true,\"popLatest\":true,\"immutable_bytes\":true,\"stop_refused\":true}\n");return 0;
}
}
