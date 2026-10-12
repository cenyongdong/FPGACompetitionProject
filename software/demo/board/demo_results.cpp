#include "demo_results.hpp"
#include <fstream>
#include <iomanip>
namespace wifi_demo {
namespace {
void bytes(const std::filesystem::path& p,const void* data,size_t count) {
    if(std::filesystem::exists(p))throw std::runtime_error("Preserve result bytes");
    std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),count);f.close();
    if(!f)throw std::runtime_error("Result bytes write failed");
}
}
void Results::add(pose_v1::Window w,pose_v1::application::Result r,uint64_t arrived,uint64_t returned) {
    if(rows_.size()>=100||r.frame_id!=w.frame_id)throw std::runtime_error("Demo result ownership/count differs");
    rows_.push_back({std::move(w),std::move(r),arrived,returned});
}
void Results::save(const std::filesystem::path& root) const {
    if(!std::filesystem::create_directory(root))throw std::runtime_error("Fresh result store required");
    std::ofstream metadata(root/"frames.jsonl");metadata<<std::setprecision(17);
    for(const auto& row:rows_) {
        const auto& r=row.result;auto d=root/("frame-"+std::to_string(r.frame_id));
        if(!std::filesystem::create_directory(d))throw std::runtime_error("Repeated result frame id");
        static_assert(sizeof(row.input.csi)==86400,"Raw complex wire layout differs");
        bytes(d/"csi.payload",row.input.csi.data(),sizeof(row.input.csi));
        bytes(d/"input.f32",r.input.data(),sizeof(r.input));bytes(d/"scores.f32",r.scores.data(),sizeof(r.scores));
        bytes(d/"poses.f32",r.poses.data(),sizeof(r.poses));
        metadata<<"{\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation<<",\"source_time_ns\":"<<r.source_time_ns
            <<",\"arrived_board_ns\":"<<row.arrived<<",\"returned_board_ns\":"<<row.returned
            <<",\"best_slot\":"<<r.best_index<<",\"best_score\":"<<r.scores[r.best_index]
            <<",\"layers\":"<<r.completed_layers<<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks
            <<",\"process_ms\":"<<r.process_ms<<",\"selected_pose\":[";
        for(size_t i=0;i<r.selected_pose.size();++i) {if(i)metadata<<',';metadata<<r.selected_pose[i];}
        metadata<<"]}\n";
    }
    metadata.close();if(!metadata)throw std::runtime_error("Result metadata write failed");
}
}
