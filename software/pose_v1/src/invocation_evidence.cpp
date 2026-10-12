#include "invocation_evidence.hpp"
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <set>
namespace pose::invocation_evidence {
namespace {
void need(bool value,const char* reason){if(!value)throw std::runtime_error(reason);}
std::string quote(const std::string& text){std::ostringstream s;s<<'"';for(unsigned char c:text){if(c=='"')s<<"\\\"";else if(c=='\\')s<<"\\\\";else if(c<32)s<<"\\u"<<std::hex<<std::setfill('0')<<std::setw(4)<<unsigned(c)<<std::dec;else s<<c;}s<<'"';return s.str();}
}
void Frame::checkOwner()const{need(std::this_thread::get_id()==owner_,"Invocation evidence owner thread changed");}
void Frame::begin(uint64_t frame,uint64_t invocation){
    checkOwner();
    if(active_&&invocation==invocation_){need(frame==frame_,"Invocation frame identity changed");return;}
    need(!active_||invocation>invocation_,"Invocation evidence regressed");
    items_.clear();total_=0;frame_=frame;invocation_=invocation;active_=true;
}
void Frame::record(int64_t op,size_t slot,std::vector<char> bytes){
    checkOwner();
    need(active_&&op>=0&&slot<4&&!bytes.empty()&&bytes.size()%4==0,"Invalid FP32 evidence identity/bytes");
    need(items_.size()<8&&bytes.size()<=1048576&&total_<=1048576-bytes.size(),"Invocation evidence budget exceeded");
    const auto key=std::make_pair(op,slot);need(!items_.count(key),"Duplicate invocation input evidence");
    total_+=bytes.size();items_.emplace(key,Item{op,slot,std::move(bytes)});
}
void Frame::save(const std::filesystem::path& dir)const{
    checkOwner();
    need(active_&&!items_.empty()&&!dir.empty()&&!std::filesystem::exists(dir),"Preserve invocation evidence");
    std::filesystem::create_directory(dir);std::ofstream index(dir/"index.json");need(bool(index),"Invocation index open failed");
    index<<"{\"frame_id\":"<<frame_<<",\"invocation\":"<<invocation_<<",\"owned_bytes\":"<<total_<<",\"source_device_read\":false,\"inputs\":[";bool first=true;
    for(const auto& pair:items_){const auto& x=pair.second;const auto name="op"+std::to_string(x.op)+".slot"+std::to_string(x.slot)+".f32";
        std::ofstream f(dir/name,std::ios::binary);f.write(x.bytes.data(),std::streamsize(x.bytes.size()));f.close();need(bool(f),"Invocation byte save failed");
        if(!first)index<<',';
        first=false;index<<"{\"op_id\":"<<x.op<<",\"slot\":"<<x.slot<<",\"bytes\":"<<x.bytes.size()<<",\"file\":"<<quote(name)<<'}';}
    index<<"]}\n";index.close();need(bool(index),"Invocation index save failed");
}
void flush(const std::vector<Task>& tasks,std::exception_ptr& original,const std::filesystem::path& ledger){
    need(!tasks.empty()&&tasks.size()<=8,"Evidence task budget differs");std::set<std::string> names;
    for(const auto& t:tasks)need(!t.name.empty()&&bool(t.persist)&&names.insert(t.name).second,"Invalid or duplicate evidence task");
    const bool alreadyFailed=bool(original);std::vector<std::pair<std::string,std::string>> outcomes;
    for(const auto& t:tasks){try{t.persist();outcomes.emplace_back(t.name,"");}catch(const std::exception& e){if(!original)original=std::current_exception();outcomes.emplace_back(t.name,e.what());}catch(...){if(!original)original=std::current_exception();outcomes.emplace_back(t.name,"Unknown persistence exception");}}
    try{need(!ledger.empty()&&!std::filesystem::exists(ledger),"Preserve evidence task ledger");std::ofstream f(ledger);need(bool(f),"Evidence task ledger open failed");f<<"{\"original_computation_failure\":"<<(alreadyFailed?"true":"false")<<",\"tasks\":[";
        for(size_t i=0;i<outcomes.size();++i){if(i)f<<',';f<<"{\"name\":"<<quote(outcomes[i].first)<<",\"saved\":"<<(outcomes[i].second.empty()?"true":"false")<<",\"error\":"<<quote(outcomes[i].second)<<'}';}f<<"]}\n";f.close();need(bool(f),"Evidence task ledger write failed");
    }catch(...){if(!original)original=std::current_exception();}
}
}
