#include "presaved_result_evidence.hpp"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <exception>
#include <iomanip>

namespace pose::validation {
namespace {
template<size_t N> void difference(std::ostream& log,const std::array<float,N>& actual,const std::array<float,N>& expected){
    size_t bits=0;bool finite=true;double maximum=0;
    for(size_t i=0;i<N;++i){
        bits+=std::memcmp(&actual[i],&expected[i],sizeof(float))!=0;
        finite=finite&&std::isfinite(actual[i]);
        if(std::isfinite(actual[i]))maximum=std::max(maximum,std::abs(double(actual[i])-double(expected[i])));
    }
    log<<"{\"bit_mismatches\":"<<bits<<",\"finite\":"<<(finite?"true":"false")<<",\"max_abs\":"<<maximum<<"}";
}
}
void saveThenVerifyResult(const FixtureWindow& c,const pose_v1::application::Result& r,
                          const pose_v1::Window& actual,size_t call,const std::filesystem::path& out,
                          std::ofstream& calls){
    const auto parent=out/"presaved-results";
    if(!std::filesystem::exists(parent))std::filesystem::create_directory(parent);
    const auto directory=parent/std::to_string(call);
    if(std::filesystem::exists(directory))throw std::runtime_error("Preserve presaved result");
    std::filesystem::create_directory(directory);
    persistBytes(directory/"input.f32",r.input.data(),sizeof(r.input));
    persistBytes(directory/"scores.f32",r.scores.data(),sizeof(r.scores));
    persistBytes(directory/"poses.f32",r.poses.data(),sizeof(r.poses));
    persistBytes(directory/"raw-payload.bin",actual.csi.data(),sizeof(actual.csi));
    std::ofstream f(directory/"identity.json");f<<std::setprecision(17);
    f<<"{\"saved_before_gate\":true,\"case\":\""<<c.name<<"\",\"call\":"<<call<<",\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation
     <<",\"before_clear\":"<<r.before_clear<<",\"before_forward\":"<<r.before_forward<<",\"completed_layers\":"<<r.completed_layers
     <<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks<<",\"input\":";
    difference(f,r.input,c.input);f<<",\"scores\":";difference(f,r.scores,c.scores);f<<",\"poses\":";difference(f,r.poses,c.poses);f<<"}\n";
    f.close();if(!f)throw std::runtime_error("Presaved result metadata write failed");
    // Same gate, exception and successful result files as the frozen adapter.
    saveVerifiedResult(c,r,call,out,calls);
}
}
