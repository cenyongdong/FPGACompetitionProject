#include "bounded_frame_reference.hpp"
#include "bounded_load_contract.hpp"
#include "skeleton_render.hpp"
#include <set>
#include <fstream>
#include <stdexcept>

namespace pose::bounded_load {
void saveFrameReferences(const std::vector<pose::measurement::Measurement>& records,
    const std::vector<pose::validation::FixtureWindow>& cases,const std::filesystem::path& out){
    std::ofstream index(out/"frames/reference-index.jsonl");
    if(!index)throw std::runtime_error("Reference index open failed");
    std::set<std::string> seen;
    for(size_t i=0;i<records.size();++i){
        const auto& r=records[i].result;
        const auto& c=pose::measurement::fixtureFor(cases,r.frame_id);
        const bool kept=keepReference(i,records.size(),seen.insert(c.name).second);
        index<<"{\"invocation\":"<<i<<",\"frame_id\":"<<r.frame_id<<",\"ARM_postrun_reconstruction\":true,\"sampled_buffer\":false,\"saved\":"<<(kept?"true":"false")<<"}\n";
        if(kept){auto rgb=pose_v1::render::draw(r.scores,r.poses,r.frame_id);
            auto pixels=pose_v1::render::yuv420sp(rgb.rgb,pose_v1::render::width,pose_v1::render::height,false);
            pose::validation::persistBytes(out/"frames"/("result"+std::to_string(i)+".nv12"),pixels.data(),pixels.size());}
    }
    index.close();if(!index)throw std::runtime_error("Reference index write failed");
}
}
