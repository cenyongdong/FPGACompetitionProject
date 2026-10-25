#include "journal.hpp"
#include <sys/socket.h>
#include <sys/wait.h>
#include <poll.h>
#include <signal.h>
#include <unistd.h>
#include <fstream>
#include <cstring>

namespace pose180_demo {
namespace {
void writer(int fd,const std::filesystem::path& output) {
    // Four rotating segments, each <=64 complete results and <=256 KiB logs.
    // Only files inside this fresh run directory are ever replaced.
    std::array<unsigned char,pp::full_bytes+1> bytes{};
    unsigned segment=0,records=64;std::size_t log_bytes=256*1024;
    std::ofstream data,log,fault;bool healthy=true;
    std::uint64_t retry_at=0;
    std::ofstream diagnostic;unsigned diagnostic_segment=0;
    std::size_t diagnostic_bytes=256*1024;
    std::uint64_t diagnostic_retry=0;
    for(;;) {
        const auto n=::recv(fd,bytes.data(),bytes.size(),0);if(n<=0)break;
        if(bytes[0]=='Q')break;
        if(bytes[0]=='D') {
            // A CSI event must outlive the rapid full-record/HDMI log rotation.
            // Whole lines, two <=256 KiB files; disk faults have their own
            // backoff and cannot suppress normal result recording.
            bool written=false;
            if(now_ns()>=diagnostic_retry)try {
                const auto size=std::size_t(n-1);
                if(!diagnostic.is_open()||diagnostic_bytes+size>256*1024) {
                    diagnostic.close();diagnostic.clear();
                    diagnostic.open(output/("diagnostic-"+std::to_string(diagnostic_segment)+".jsonl"),std::ios::trunc);
                    diagnostic_segment=(diagnostic_segment+1)%2;diagnostic_bytes=0;
                }
                diagnostic.write(reinterpret_cast<char*>(bytes.data()+1),size);diagnostic.flush();
                if(!diagnostic)throw std::runtime_error("CSI diagnostic archive unavailable");
                diagnostic_bytes+=size;written=true;
            }catch(...){diagnostic.close();diagnostic.clear();diagnostic_retry=now_ns()+5000000000ull;}
            const char state=written?'1':'0';::send(fd,&state,1,MSG_DONTWAIT|MSG_NOSIGNAL);
            continue;
        }
        try {
            if(bytes[0]=='F') {
                if(!fault.is_open())fault.open(output/"fault-ring.full",std::ios::binary|std::ios::out);
                fault.write(reinterpret_cast<char*>(bytes.data()+1),n-1);fault.flush();
                if(!fault)throw std::runtime_error("fault archive unavailable");
                continue;
            }
            if(!healthy && now_ns()<retry_at)continue;
            if(records>=64 || log_bytes>=256*1024 || !healthy) {
                data.close();log.close();data.clear();log.clear();
                data.open(output/("recent-"+std::to_string(segment)+".full"),std::ios::binary|std::ios::trunc);
                log.open(output/("recent-"+std::to_string(segment)+".jsonl"),std::ios::trunc);
                segment=(segment+1)%4;records=0;log_bytes=0;
                if(!data || !log)throw std::runtime_error("recorder unavailable");
            }
            if(bytes[0]=='R') {data.write(reinterpret_cast<char*>(bytes.data()+1),n-1);data.flush();++records;}
            else {log.write(reinterpret_cast<char*>(bytes.data()+1),n-1);log.flush();log_bytes+=n-1;}
            if(!data||!log)throw std::runtime_error("recorder write failed");
            healthy=true;
        }catch(...){healthy=false;retry_at=now_ns()+5000000000ull;}
        const char state=healthy?'1':'0';::send(fd,&state,1,MSG_DONTWAIT|MSG_NOSIGNAL);
    }
}
}
Journal::Journal(Shared& s,const std::filesystem::path& path):shared_(s) {
    setp(line_.data(),line_.data()+line_.size());
    int pair[2];if(::socketpair(AF_UNIX,SOCK_SEQPACKET|SOCK_CLOEXEC,0,pair))throw std::runtime_error("Recorder IPC failed");
    child_=::fork();
    if(child_==0){::close(pair[0]);writer(pair[1],path);::close(pair[1]);::_exit(0);}
    ::close(pair[1]);fd_=pair[0];
    if(child_<0){::close(fd_);fd_=-1;throw std::runtime_error("Recorder fork failed");}
}
void Journal::send(unsigned char type,const void* data,std::size_t size) {
    std::array<unsigned char,pp::full_bytes+1> bytes{};bytes[0]=type;
    if(size>pp::full_bytes)return;
    std::memcpy(bytes.data()+1,data,size);
    if(::send(fd_,bytes.data(),size+1,MSG_DONTWAIT|MSG_NOSIGNAL)!=ssize_t(size+1)) {
        ++shared_.stats.record_dropped;shared_.stats.recording=false;
    }
    char reply;while(::recv(fd_,&reply,1,MSG_DONTWAIT)>0)shared_.stats.recording=reply=='1';
}
void Journal::record(const Record& record) {
    ring_[next_]=record;next_=(next_+1)%ring_.size();count_=std::min(count_+1,ring_.size());send('R',record.data(),record.size());
}
void Journal::freeze() {
    for(std::size_t i=0;i<count_;++i){const auto& r=ring_[(next_+ring_.size()-count_+i)%ring_.size()];send('F',r.data(),r.size());}
}
void Journal::status(const std::string& text){send('L',text.data(),std::min(text.size(),line_.size()));}
void Journal::diagnostic(const std::string& text) {
    if(text.size()>1024){++shared_.stats.diagnostic_dropped;return;}
    send('D',text.data(),text.size());
}
int Journal::sync(){if(pptr()!=pbase())send('L',pbase(),pptr()-pbase());setp(line_.data(),line_.data()+line_.size());return 0;}
Journal::int_type Journal::overflow(int_type c){sync();if(!traits_type::eq_int_type(c,traits_type::eof())){*pptr()=traits_type::to_char_type(c);pbump(1);}return traits_type::not_eof(c);}
Journal::~Journal() {
    sync();send('Q',"",0);::close(fd_);
    // The child has never inherited SDK/device handles. Stalled normal logging
    // can be terminated independently without touching the inference process.
    for(int i=0;i<20;++i){if(::waitpid(child_,nullptr,WNOHANG)==child_)return;::usleep(10000);}
    ::kill(child_,SIGTERM);
    for(int i=0;i<20;++i){if(::waitpid(child_,nullptr,WNOHANG)==child_)return;::usleep(10000);}
    ::kill(child_,SIGKILL);::waitpid(child_,nullptr,0);
}
}
