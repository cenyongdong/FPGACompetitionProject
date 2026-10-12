#include "final_source_recorder.hpp"
#include <chrono>
#include <fstream>
#include <iomanip>
#include <stdexcept>
namespace pose::final_source {
namespace {
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
uint64_t now(){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count();}
void bytes(const std::filesystem::path&p,const std::vector<char>&b){need(!std::filesystem::exists(p),"Preserve recorder file");std::ofstream f(p,std::ios::binary);f.write(b.data(),b.size());need(bool(f),"Recorder bytes write failed");}
std::string stem(int64_t op,size_t slot){return std::to_string(op)+"."+std::to_string(slot);}
}
void Recorder::owner()const{need(owner_==std::this_thread::get_id(),"Recorder thread owner differs");}
void Recorder::begin(uint64_t f,uint64_t i){owner();need(!captured_,"Recorder stopped after capture");if(begun_){need(i==invocation_+1,"Recorder invocation sequence differs");}sources_.clear();outputs_.clear();frame_=f;invocation_=i;begun_=true;}
void Recorder::source(int64_t op,size_t slot,std::string metadata,std::vector<char> host,Reader read){
    owner();need(begun_&&!captured_,"Recorder frame not active");need((op==582||op==649)&&slot<2&&host.size()==16800&&bool(read)&&metadata.size()<16384,"Recorder source bound differs");
    need(sources_.size()<4&&sources_.emplace(Key{op,slot},Source{std::move(metadata),std::move(host),std::move(read)}).second,"Recorder duplicate source");
}
void Recorder::output(int64_t op,size_t slot,std::vector<char> owned){
    owner();need(begun_&&!captured_,"Recorder frame not active");need((op==437&&slot<2&&owned.size()==400)||(op==582&&slot==0&&owned.size()==16800),"Recorder CPU output bound differs");
    need(outputs_.size()<3&&outputs_.emplace(Key{op,slot},std::move(owned)).second,"Recorder duplicate CPU output");
}
void Recorder::capture(const std::filesystem::path& directory,const std::string& original){
    owner();need(begun_&&!captured_,"Recorder capture unavailable");need(!std::filesystem::exists(directory)&&std::filesystem::is_directory(directory.parent_path()),"Preserve recorder directory");captured_=true;
    // Allocate all buffers first. No file IO between the two read rounds.
    struct Read {Key key;size_t round;std::vector<char> data;uint64_t begin=0,end=0;bool complete=false;std::string error;};
    std::vector<Read> reads;for(size_t round=0;round<2;++round)for(const auto&s:sources_)reads.push_back({s.first,round,std::vector<char>(s.second.host.size()),0,0,false,{}});
    std::string captureError;
    for(auto&r:reads){r.begin=now();try{sources_.at(r.key).read(r.data.data(),r.data.size());r.complete=true;}catch(const std::exception&e){r.error=e.what();captureError=r.error;}catch(...){r.error="Unknown public read failure";captureError=r.error;}r.end=now();if(!r.complete)break;}
    std::filesystem::create_directory(directory);
    for(const auto&s:sources_)bytes(directory/("host."+stem(s.first.first,s.first.second)+".f32"),s.second.host);
    for(const auto&s:outputs_)bytes(directory/("cpu."+stem(s.first.first,s.first.second)+".f32"),s.second);
    for(const auto&r:reads)if(r.complete)bytes(directory/("round"+std::to_string(r.round)+"."+stem(r.key.first,r.key.second)+".f32"),r.data);
    std::ofstream f(directory/"index.json");f<<"{\"frame\":"<<frame_<<",\"invocation\":"<<invocation_<<",\"original_error\":"<<std::quoted(original)<<",\"capture_error\":"<<std::quoted(captureError)<<",\"physical_reuse_possible\":true,\"no_forward_or_reset\":true,\"sources\":[";
    bool first=true;for(const auto&s:sources_){if(!first)f<<',';first=false;f<<"{\"op\":"<<s.first.first<<",\"slot\":"<<s.first.second<<",\"bytes\":"<<s.second.host.size()<<",\"storage\":"<<s.second.metadata<<'}';}f<<"],\"cpu_outputs\":[";
    first=true;for(const auto&s:outputs_){if(!first)f<<',';first=false;f<<"{\"op\":"<<s.first.first<<",\"slot\":"<<s.first.second<<",\"bytes\":"<<s.second.size()<<'}';}f<<"],\"reads\":[";
    first=true;for(const auto&r:reads){if(!first)f<<',';first=false;f<<"{\"round\":"<<r.round<<",\"op\":"<<r.key.first<<",\"slot\":"<<r.key.second<<",\"begin_ns\":"<<r.begin<<",\"end_ns\":"<<r.end<<",\"complete\":"<<(r.complete?"true":"false")<<",\"error\":"<<std::quoted(r.error)<<'}';}f<<"]}\n";f.close();need(bool(f),"Recorder metadata write failed");
}
}
