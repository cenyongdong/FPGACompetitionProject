#include "read_phase.hpp"
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
namespace pose::read_phase {
namespace {
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
uint64_t hash(const std::vector<char>&b){uint64_t h=14695981039346656037ULL;for(unsigned char c:b){h^=c;h*=1099511628211ULL;}return h;}
std::string quote(const std::string&s){std::ostringstream f;f<<'"';for(unsigned char c:s){switch(c){case '"':f<<"\\\"";break;case '\\':f<<"\\\\";break;case '\n':f<<"\\n";break;case '\r':f<<"\\r";break;case '\t':f<<"\\t";break;default:if(c<32)f<<"\\u00"<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(c)<<std::dec;else f<<char(c);}}f<<'"';return f.str();}
void blob(const std::filesystem::path&p,const std::vector<char>&b){std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());need(bool(f),"Read phase byte write failed");}
}
void Evidence::owner()const{need(owner_==std::this_thread::get_id(),"Read phase owner differs");}
void Evidence::begin(uint64_t f,uint64_t i,uint64_t t,std::string id){
    owner();need(!saved_&&rows_.size()<103&&i==rows_.size()&&id.size()<16384,"Read phase invocation/bound differs");
    if(!rows_.empty()&&rows_.back().invocation<4)first_.push_back(std::move(current_));
    current_=Owned{i,{},{}};current_.immediate.reserve(16800);current_.beforeCPU.reserve(16800);Row r;r.frame=f;r.invocation=i;r.begin=t;r.before=std::move(id);rows_.push_back(std::move(r));
}
void Evidence::readDone(uint64_t t,std::string id,const char*b,size_t n){
    owner();need(!saved_&&!rows_.empty()&&!rows_.back().readDone&&b&&n==16800&&id.size()<16384&&t>=rows_.back().begin,"Read phase completion differs");
    current_.immediate.assign(b,b+n);auto&r=rows_.back();r.end=t;r.after=std::move(id);r.readHash=hash(current_.immediate);r.readDone=true;
}
void Evidence::beforeCPU(uint64_t t,std::string id,const char*b,size_t n){
    owner();need(!saved_&&!rows_.empty()&&rows_.back().readDone&&!rows_.back().cpuDone&&b&&n==16800&&id.size()<16384&&t>=rows_.back().end,"Read phase CPU boundary differs");
    current_.beforeCPU.assign(b,b+n);auto&r=rows_.back();r.cpu=t;r.atCPU=std::move(id);r.cpuHash=hash(current_.beforeCPU);r.cpuDone=true;
    for(size_t i=0;i<n;++i)r.changed+=current_.immediate[i]!=current_.beforeCPU[i];
}
void Evidence::error(uint64_t t,std::string message){owner();need(!saved_&&!rows_.empty()&&message.size()<32768,"Read phase error bound differs");rows_.back().errorTime=t;rows_.back().error=std::move(message);}
void Evidence::identityAfterSnapshot(bool cpu,std::string id){owner();need(!saved_&&!rows_.empty()&&id.size()<16384&&(cpu?rows_.back().cpuDone:rows_.back().readDone),"Read phase identity stage differs");(cpu?rows_.back().atCPU:rows_.back().after)=std::move(id);}
void Evidence::save(const std::filesystem::path&p){
    owner();need(!saved_&&!rows_.empty()&&!std::filesystem::exists(p)&&std::filesystem::is_directory(p.parent_path()),"Preserve read phase evidence");saved_=true;std::filesystem::create_directory(p);
    std::ofstream f(p/"metadata.jsonl");for(const auto&r:rows_){
        f<<"{\"frame\":"<<r.frame<<",\"invocation\":"<<r.invocation<<",\"read_begin_ns\":"<<r.begin<<",\"read_return_ns\":"<<r.end<<",\"before_CPU_ns\":"<<r.cpu<<",\"error_ns\":"<<r.errorTime<<",\"read_done\":"<<(r.readDone?"true":"false")<<",\"cpu_snapshot_done\":"<<(r.cpuDone?"true":"false")<<",\"byte_changes\":"<<r.changed<<",\"immediate_FNV64_diagnostic_only\":"<<r.readHash<<",\"CPU_FNV64_diagnostic_only\":"<<r.cpuHash<<",\"before_identity\":"<<r.before<<",\"after_identity\":"<<(r.after.empty()?"null":r.after)<<",\"CPU_identity\":"<<(r.atCPU.empty()?"null":r.atCPU)<<",\"error\":"<<quote(r.error)<<"}\n";
    }f.close();need(bool(f),"Read phase metadata write failed");
    auto write=[&](const Owned& o){auto d=p/("frame"+std::to_string(o.invocation));std::filesystem::create_directory(d);if(!o.immediate.empty())blob(d/"immediate.f32",o.immediate);if(!o.beforeCPU.empty())blob(d/"before-CPU.f32",o.beforeCPU);};
    for(const auto&o:first_)write(o);
    write(current_);std::ofstream s(p/"summary.json");s<<"{\"rows\":"<<rows_.size()<<",\"last_invocation\":"<<rows_.back().invocation<<",\"first_frames\":"<<first_.size()<<",\"per_frame_bytes\":33600,\"no_second_read\":true,\"no_repair\":true}\n";need(bool(s),"Read phase summary failed");
}
}
