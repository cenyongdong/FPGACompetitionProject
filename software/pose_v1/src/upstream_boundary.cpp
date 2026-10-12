#include "upstream_boundary.hpp"
#include <fstream>
#include <iomanip>
#include <stdexcept>
#include <sstream>
namespace pose::upstream {
namespace {
void need(bool b,const char*s){if(!b)throw std::runtime_error(s);}
std::pair<int64_t,size_t> spec(const std::string&p){
    if(p=="topk_indices"||p=="gather_pre_indices")return {1137,400};
    if(p=="zg_input_data"||p=="gather_pre_data")return {4406,16800};
    if(p=="gather_post"||p=="zg_pre_gather")return {1148,16800};
    if(p=="zg_post_base")return {4414,16800};
    if(p=="zg_post_update")return {4418,16800};
    throw std::runtime_error("Unknown boundary point");
}
uint64_t hash(const std::vector<char>&b){uint64_t h=14695981039346656037ULL;for(unsigned char x:b){h^=x;h*=1099511628211ULL;}return h;}
void data(const std::filesystem::path&p,const std::vector<char>&b){std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());need(bool(f),"Boundary bytes write failed");}
}
std::string quoted(const std::string&s){std::ostringstream f;f<<'"';for(unsigned char c:s){switch(c){case '"':f<<"\\\"";break;case '\\':f<<"\\\\";break;case '\n':f<<"\\n";break;case '\r':f<<"\\r";break;case '\t':f<<"\\t";break;default:if(c<32)f<<"\\u00"<<std::hex<<std::setw(2)<<std::setfill('0')<<unsigned(c)<<std::dec;else f<<char(c);}}f<<'"';return f.str();}
void Evidence::owner()const{need(owner_==std::this_thread::get_id(),"Boundary owner thread differs");}
void Evidence::begin(uint64_t f,uint64_t i){owner();need(!saved_&&i<103,"Boundary stopped or frame limit");need(active_?i==invocation_+1:i==0,"Boundary invocation differs");if(active_&&invocation_<4)first_.push_back({frame_,invocation_,std::move(current_)});current_.clear();frame_=f;invocation_=i;active_=true;}
void Evidence::record(Sample s){owner();need(active_&&!saved_,"Boundary frame not active");auto wanted=spec(s.point);need(s.value==wanted.first&&s.storage.size()<16384&&s.error.size()<32768,"Boundary metadata bound differs");need(s.error.empty()?s.bytes.size()==wanted.second:s.bytes.empty(),"Boundary owned byte bound differs");need(current_.size()<8&&!current_.count(s.point)&&rows_.size()<824,"Boundary duplicate/sample bound");Row row{frame_,invocation_,hash(s.bytes),s,s.bytes.size()};row.metadata.bytes.clear();rows_.push_back(std::move(row));current_.emplace(s.point,std::move(s));}
void Evidence::save(const std::filesystem::path&p){owner();need(active_&&!saved_&&!std::filesystem::exists(p)&&std::filesystem::is_directory(p.parent_path()),"Preserve boundary directory");saved_=true;std::filesystem::create_directory(p);std::ofstream f(p/"metadata.jsonl");need(bool(f),"Boundary metadata open failed");
    for(const auto&r:rows_){const auto&s=r.metadata;f<<"{\"frame\":"<<r.frame<<",\"invocation\":"<<r.invocation<<",\"point\":"<<quoted(s.point)<<",\"value\":"<<s.value<<",\"bytes\":"<<r.bytes<<",\"FNV64_diagnostic_only\":"<<r.hash<<",\"wait_begin_ns\":"<<s.waitBegin<<",\"wait_end_ns\":"<<s.waitEnd<<",\"read_begin_ns\":"<<s.readBegin<<",\"read_end_ns\":"<<s.readEnd<<",\"count_before\":"<<s.countBefore<<",\"count_after\":"<<s.countAfter<<",\"storage\":"<<s.storage<<",\"error\":"<<quoted(s.error)<<"}\n";}f.close();need(bool(f),"Boundary metadata write failed");
    auto write=[&](uint64_t frame,uint64_t inv,const std::map<std::string,Sample>&samples){auto dir=p/("frame"+std::to_string(inv));std::filesystem::create_directory(dir);std::ofstream index(dir/"index.json");index<<"{\"frame\":"<<frame<<",\"invocation\":"<<inv<<",\"samples\":[";bool first=true;for(const auto&x:samples){if(!first)index<<',';first=false;index<<quoted(x.first);if(!x.second.bytes.empty())data(dir/(x.first+".f32"),x.second.bytes);}index<<"]}\n";need(bool(index),"Boundary frame index write failed");};
    for(const auto&x:first_){write(x.frame,x.invocation,x.samples);}
    write(frame_,invocation_,current_);
    std::ofstream summary(p/"summary.json");summary<<"{\"rows\":"<<rows_.size()<<",\"first_frames_saved\":"<<first_.size()<<",\"last_invocation\":"<<invocation_<<",\"maximum_owned_frame_bytes\":101600,\"retained_producer_not_private_session_input\":true,\"physical_reuse_possible\":true,\"pre_callback_vector_not_read_as_inputs\":true}\n";need(bool(summary),"Boundary summary write failed");
}
}
