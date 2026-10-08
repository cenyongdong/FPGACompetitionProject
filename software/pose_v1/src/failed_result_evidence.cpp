#include "failed_result_evidence.hpp"
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
void saveOrCaptureFailedResult(const FixtureWindow& c,const pose_v1::application::Result& r,
                               const pose_v1::Window& actual,size_t call,const std::filesystem::path& out,
                               std::ofstream& calls){
    try{saveVerifiedResult(c,r,call,out,calls);}
    catch(...){
        const auto original=std::current_exception();
        try{
            const auto directory=out/"failed-result";
            if(std::filesystem::exists(directory))std::rethrow_exception(original);
            std::filesystem::create_directory(directory);
            persistBytes(directory/"input.f32",r.input.data(),sizeof(r.input));
            persistBytes(directory/"scores.f32",r.scores.data(),sizeof(r.scores));
            persistBytes(directory/"poses.f32",r.poses.data(),sizeof(r.poses));
            persistBytes(directory/"raw-payload.bin",actual.csi.data(),sizeof(actual.csi));
            std::ofstream f(directory/"identity.json");f<<std::setprecision(17);
            f<<"{\"case\":\""<<c.name<<"\",\"call\":"<<call<<",\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation
             <<",\"before_clear\":"<<r.before_clear<<",\"before_forward\":"<<r.before_forward<<",\"completed_layers\":"<<r.completed_layers
             <<",\"host_callbacks\":"<<r.host_callbacks<<",\"zg_callbacks\":"<<r.zg_callbacks<<",\"input\":";
            difference(f,r.input,c.input);f<<",\"scores\":";difference(f,r.scores,c.scores);f<<",\"poses\":";difference(f,r.poses,c.poses);f<<"}\n";
            if(!f)throw std::runtime_error("Failed result metadata write failed");
        }catch(...){/* Preserve the original stop reason even if evidence I/O fails. */}
        std::rethrow_exception(original);
    }
}
}
