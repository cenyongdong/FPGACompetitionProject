#include "pipeline_fixture_source.hpp"
#include <cstring>
#include <cmath>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace pose::validation {
namespace {
void check(bool ok,const char* text){if(!ok)throw std::runtime_error(text);}
void read(const std::filesystem::path& path,void* data,size_t n){
    check(std::filesystem::file_size(path)==n,"Fixture byte count differs");
    std::ifstream f(path,std::ios::binary);check(bool(f.read(static_cast<char*>(data),n)),"Fixture read failed");
}
}
void persistBytes(const std::filesystem::path& p,const void* data,size_t n){
    std::ofstream f(p,std::ios::binary);f.write(static_cast<const char*>(data),n);check(bool(f),"Result evidence write failed");
}
std::vector<FixtureWindow> fixtureWindows(const std::filesystem::path& package,bool expanded){
    std::ifstream f(package/"cases.tsv");check(bool(f),"Fixture catalog missing");std::vector<FixtureWindow> cases;std::string line;
    while(std::getline(f,line)){
        std::istringstream row(line);std::string group,name,extra;uint64_t frame,time;
        check(bool(row>>group>>name>>frame>>time)&&!(row>>extra),"Fixture catalog row invalid");
        if(group!=(expanded?"expanded":"base"))continue;
        check(name.find_first_not_of("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")==std::string::npos,"Unsafe fixture name");
        FixtureWindow c;c.name=name;c.window=pose_v1::read_window((package/"inputs"/(name+".csi")).string());
        check(c.window.frame_id==frame&&c.window.source_time_ns==time,"Fixture identity differs");
        read(package/"reference"/(name+".input.f32"),c.input.data(),sizeof(c.input));
        read(package/"r6-reference"/(name+".scores.f32"),c.scores.data(),sizeof(c.scores));
        read(package/"r6-reference"/(name+".poses.f32"),c.poses.data(),sizeof(c.poses));cases.push_back(std::move(c));
    }
    check(cases.size()==(expanded?27:3),"Fixture coverage differs");cases.push_back(cases.front());return cases;
}
void saveVerifiedResult(const FixtureWindow& c,const pose_v1::application::Result& r,size_t i,const std::filesystem::path& out,std::ofstream& log){
    check(!r.frozen_reference_checked&&r.invocation==i&&r.frame_id==c.window.frame_id,"Engine invocation/reference mode differs");
    check(std::memcmp(r.input.data(),c.input.data(),sizeof(r.input))==0,"Actual PS input differs");
    check(std::memcmp(r.scores.data(),c.scores.data(),sizeof(r.scores))==0&&std::memcmp(r.poses.data(),c.poses.data(),sizeof(r.poses))==0,"Actual model outputs differ");
    check(r.before_forward==0&&r.completed_layers==745&&r.host_callbacks==7&&r.zg_callbacks==7,"Frame completion protocol differs");
    for(auto value:r.scores)check(std::isfinite(value),"Nonfinite score");
    for(auto value:r.poses)check(std::isfinite(value),"Nonfinite pose");
    const auto stem="result"+std::to_string(i);persistBytes(out/(stem+".input.f32"),r.input.data(),sizeof(r.input));
    persistBytes(out/(stem+".scores.f32"),r.scores.data(),sizeof(r.scores));persistBytes(out/(stem+".poses.f32"),r.poses.data(),sizeof(r.poses));
    log<<std::setprecision(17)<<"{\"call\":"<<i<<",\"case\":\""<<c.name<<"\",\"frame_id\":"<<r.frame_id<<",\"invocation\":"<<r.invocation
        <<",\"before_forward\":0,\"completed_layers\":745,\"host_callbacks\":7,\"zg_callbacks\":7,\"best_index\":"<<r.best_index<<",\"process_ms\":"<<r.process_ms<<"}"<<std::endl;
    check(bool(log),"Result trace write failed");
}
}
