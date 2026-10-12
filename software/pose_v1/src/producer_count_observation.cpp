#include "producer_count_observation.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <memory>
#include <sstream>
#include <stdexcept>
namespace pose::producer_count {
namespace {
void need(bool yes,const char* message){if(!yes)throw std::runtime_error(message);}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
std::string quote(const std::string& text){std::ostringstream s;s<<'"';for(unsigned char c:text){if(c=='"')s<<"\\\"";else if(c=='\\')s<<"\\\\";else if(c<32)s<<"\\u"<<std::hex<<std::setw(4)<<std::setfill('0')<<unsigned(c)<<std::dec;else s<<c;}s<<'"';return s.str();}
const char* name(Point p){switch(p){case Point::BeforeWait:return "before_wait";case Point::AfterWait:return "after_wait";case Point::BeforeCopy:return "before_copy";case Point::AfterCopy:return "after_copy";}return "invalid";}
bool same(const Source&a,const Source&b){return a.producer==b.producer&&a.address==b.address&&a.offset==b.offset&&a.capacity==b.capacity&&a.bytes==b.bytes&&a.kind==b.kind&&a.region==b.region;}
std::filesystem::path root;std::unique_ptr<Recorder> recorder;
}
void Recorder::sample(uint64_t frame,uint64_t invocation,size_t slot,Point point,const Source& source,const std::function<uint32_t()>& read){
    need(std::this_thread::get_id()==owner_,"Producer observation owner changed");
    need(!failed_&&slot<2&&unsigned(point)<4&&bool(read),"Producer observation identity/callback differs");
    need(source.producer==(slot?8631:8629)&&source.bytes==(slot?16800:30240)&&source.offset<=source.capacity&&source.bytes<=source.capacity-source.offset,"Producer source identity/bounds differ");
    need((source.kind=="ADDR"||source.kind=="BOTH"||source.kind=="CPTR")&&!source.region.empty(),"Producer source memory identity differs");
    need(rows_.size()<824,"Producer observation budget exceeded");
    if(!active_||invocation!=invocation_){
        need(!active_||(invocation>invocation_&&next_==8),"Producer invocation regressed/incomplete");
        frame_=frame;invocation_=invocation;active_=true;next_=0;previous_=0;
    }
    need(frame==frame_&&next_==slot*4+unsigned(point),"Producer frame/point order differs");
    if(point==Point::BeforeWait)sources_[slot]=source;
    else need(same(source,sources_[slot]),"Producer source changed during observation");
    Row row{frame,invocation,now(),0,slot,point,source,0,false,{}};
    try{
        row.count=read();row.completed=true;row.end=now();
        need(row.count<=745&&row.count>=previous_,"Producer count range/regression");
        previous_=row.count;++next_;rows_.push_back(std::move(row));
    }catch(const std::exception& e){row.end=now();row.error=e.what();failed_=true;rows_.push_back(std::move(row));throw;}
    catch(...){row.end=now();row.error="Unknown producer query exception";failed_=true;rows_.push_back(std::move(row));throw;}
}
void Recorder::save(const std::filesystem::path& directory)const{
    need(std::this_thread::get_id()==owner_,"Producer persistence owner changed");
    need(!directory.empty()&&!std::filesystem::exists(directory),"Preserve producer observations");
    std::filesystem::create_directory(directory);std::ofstream f(directory/"counts.jsonl");
    for(const auto&r:rows_){f<<"{\"frame_id\":"<<r.frame<<",\"invocation\":"<<r.invocation<<",\"op_id\":192,\"slot\":"<<r.slot<<",\"point\":"<<quote(name(r.point))<<",\"producer\":"<<r.source.producer<<",\"group\":9186,\"target\":234,\"maximum\":745,\"begin_ns\":"<<r.begin<<",\"end_ns\":"<<r.end<<",\"read_completed\":"<<(r.completed?"true":"false")<<",\"count\":";
        if(r.completed)f<<r.count;else f<<"null";
        f<<",\"error\":"<<quote(r.error)<<",\"source_kind\":"<<quote(r.source.kind)<<",\"source_region\":"<<quote(r.source.region)<<",\"source_address\":"<<r.source.address<<",\"source_offset\":"<<r.source.offset<<",\"source_capacity\":"<<r.source.capacity<<",\"bytes\":"<<r.source.bytes<<",\"wait_added\":false,\"device_data_read_added\":false,\"DMA_cache_fence_proven\":false}\n";
    }f.close();need(bool(f),"Producer observation save failed");
}
void configure(const std::filesystem::path& directory){need(!recorder&&!directory.empty()&&!std::filesystem::exists(directory),"Preserve producer observation configuration");root=directory;recorder=std::make_unique<Recorder>();}
void sample(uint64_t frame,uint64_t invocation,size_t slot,Point point,const Source& source,const std::function<uint32_t()>& read){need(bool(recorder),"Producer observation not configured");recorder->sample(frame,invocation,slot,point,source,read);}
void save(){if(recorder)recorder->save(root);}
}
