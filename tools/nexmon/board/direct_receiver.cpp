// Linux PS receiver. Three router streams go directly to this board process.
// Finite one-job software candidate: no boot changes, display or PC ACK path.
#include "ingress.hpp"
#include "pcap_stream.hpp"
#include "aligned_csi.hpp"
#ifdef NEXMON_WITH_NPU
#include "pose180_runtime.hpp"
#endif
#include <arpa/inet.h>
#include <poll.h>
#include <sys/socket.h>
#include <unistd.h>
#include <algorithm>
#include <atomic>
#include <cerrno>
#include <chrono>
#include <condition_variable>
#include <deque>
#include <filesystem>
#include <fstream>
#include <future>
#include <iomanip>
#include <iostream>
#include <map>
#include <mutex>
#include <sstream>
#include <thread>

namespace nb = nexmon_board;
namespace fs = std::filesystem;
using Clock = std::chrono::steady_clock;
namespace {
void need(bool condition, const std::string& message) {
    if (!condition) throw std::runtime_error(message);
}
std::string json_string(const std::string& value) {
    std::ostringstream out; out << '"';
    for (unsigned char c : value) {
        if (c=='"' || c=='\\') out << '\\' << c;
        else if (c<32) out << "\\u" << std::hex << std::setw(4) << std::setfill('0') << unsigned(c) << std::dec;
        else out << c;
    }
    return out.str()+'"';
}
std::uint64_t now_ns() {
    return std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now().time_since_epoch()).count();
}
std::vector<std::string> split(const std::string& value) {
    std::vector<std::string> out; std::istringstream in(value); std::string s;
    while (std::getline(in,s,',')) out.push_back(s);
    return out;
}
struct Options {
    nb::Config config;
    std::string bind, model;
    std::array<std::string,3> peers;
    fs::path output;
    unsigned port=39033, seconds=30;
    bool simulation=false;
};
Options options(int argc,char** argv) {
    std::map<std::string,std::string> args;
    Options o;
    for (int i=1;i<argc;++i) {
        std::string key=argv[i];
        if (key=="--simulation") { o.simulation=true; continue; }
        need(i+1<argc && key.rfind("--",0)==0,"Expected --option value");
        need(args.emplace(key,argv[++i]).second,"Repeated option");
    }
    const auto take=[&](const char* key) { auto it=args.find(key); need(it!=args.end(),std::string("Missing ")+key);
        auto value=it->second; args.erase(it); return value; };
    o.bind=take("--bind");o.output=take("--output");o.config.session_id=take("--session");
    auto peers=split(take("--peers"));auto gains=split(take("--gains"));
    need(peers.size()==3 && gains.size()==3,"Require exactly three peers and explicit candidate gains");
    for (unsigned i=0;i<3;++i) {o.peers[i]=peers[i];o.config.receiver_ids[i]="rx"+std::to_string(i+1);
        std::size_t used=0;o.config.gains[i]=std::stod(gains[i],&used);need(used==gains[i].size(),"Invalid gain");}
    auto mac=take("--source");need(mac.size()==17,"Require six-byte transmitter MAC");
    for(unsigned i=0;i<6;++i) {std::size_t used=0;auto n=std::stoul(mac.substr(i*3,2),&used,16);
        need(used==2 && n<=255 && (i==5 || mac[i*3+2]==':'),"Invalid transmitter MAC");o.config.transmitter_mac[i]=std::uint8_t(n);}
    auto channel=take("--channel");std::size_t used=0;auto ch=std::stoul(channel,&used,0);
    need(used==channel.size() && ch<=65535,"Invalid channel");o.config.chanspec=std::uint16_t(ch);
    for(auto key:{"--port","--seconds"}) if(args.count(key)) {auto s=take(key);std::size_t n=0;auto value=std::stoul(s,&n);
        need(n==s.size() && value<=65535,"Invalid numeric option");
        if(std::string(key)=="--port")o.port=unsigned(value);else o.seconds=unsigned(value);}
    if(args.count("--model"))o.model=take("--model");
    need(args.empty(),"Unknown option");need(o.port>=1024 && o.port<=65535 && o.seconds>0 && o.seconds<=120,"Invalid finite network budget");
    need(o.peers[0]!=o.peers[1] && o.peers[1]!=o.peers[2] && o.peers[0]!=o.peers[2],"Duplicate receiver address");
    for(const auto& ip:std::vector<std::string>{o.bind,o.peers[0],o.peers[1],o.peers[2]}) {
        in_addr a{};need(inet_pton(AF_INET,ip.c_str(),&a)==1,"Invalid IPv4 address");auto n=ntohl(a.s_addr);
        bool local=(n>>24)==10 || (n>>16)==0xc0a8 || (n>>20)==0xac1 || (o.simulation && (n>>24)==127);
        need(local,"Only explicitly owned private endpoints, or explicit loopback simulation, are accepted");
    }
#ifndef NEXMON_WITH_NPU
    need(o.model.empty(),"This SDK-free executable cannot run inference");
#endif
    return o;
}
struct Fd {
    int value=-1;
    ~Fd(){if(value>=0)::close(value);}
    void close(){if(value>=0){::close(value);value=-1;}}
};
struct Job {std::uint64_t frame=0;pose_v1::Tokens tokens{};};
class Worker {
    std::mutex mutex_;std::condition_variable wake_;std::deque<Job> queue_;
    std::exception_ptr failure_;bool closed_=false,cancelled_=false;std::thread thread_;
    std::atomic<std::size_t> completed_{0};std::promise<void> ready_;
public:
    Worker(const Options& o) {
        auto initialized=ready_.get_future();
        thread_=std::thread([this,o] {
            bool initialized=false;
            try {
#ifdef NEXMON_WITH_NPU
                nb::Pose180Runtime runtime(o.model,(o.output/"model-output").string());
                std::ofstream results(o.output/"poses.jsonl");results<<std::setprecision(17);
                ready_.set_value();initialized=true;
                for(;;) {
                    Job job;
                    {std::unique_lock<std::mutex> lock(mutex_);wake_.wait(lock,[&]{return cancelled_||closed_||!queue_.empty();});
                        if(cancelled_ || (closed_&&queue_.empty()))break;
                        job=std::move(queue_.front());queue_.pop_front();}
                    auto result=runtime.infer(job.tokens);
                    results<<"{\"frame\":"<<job.frame<<",\"invocation\":"<<result.invocation
                        <<",\"best_index\":"<<result.best_index<<",\"score\":"<<result.scores[result.best_index]
                        <<",\"joints\":[";
                    for(std::size_t i=0;i<42;++i){if(i)results<<',';results<<result.poses[result.best_index*42+i];}
                    results<<"]}\n";results.flush();need(bool(results),"Local pose save failed");++completed_;
                }
#else
                (void)o;throw std::runtime_error("SDK runtime unavailable");
#endif
            } catch(...) {
                auto error=std::current_exception();{std::lock_guard<std::mutex> lock(mutex_);failure_=error;cancelled_=true;queue_.clear();}
                if(!initialized)ready_.set_exception(error);
                wake_.notify_all();
            }
        });
        try {initialized.get();} catch(...) {if(thread_.joinable())thread_.join();throw;}
    }
    ~Worker(){cancel();if(thread_.joinable())thread_.join();}
    bool push(Job job) {std::lock_guard<std::mutex> lock(mutex_);if(failure_)std::rethrow_exception(failure_);
        if(queue_.size()>=8)return false;
        queue_.push_back(std::move(job));wake_.notify_one();return true;}
    void check(){std::lock_guard<std::mutex> lock(mutex_);if(failure_)std::rethrow_exception(failure_);}
    void finish(){{std::lock_guard<std::mutex> lock(mutex_);closed_=true;}wake_.notify_all();if(thread_.joinable())thread_.join();check();}
    void cancel(){{std::lock_guard<std::mutex> lock(mutex_);cancelled_=true;queue_.clear();}wake_.notify_all();}
    std::size_t completed()const{return completed_;}
};
}

int main(int argc,char** argv) {
    fs::path output;std::unique_ptr<Worker> worker;
    try {
        auto o=options(argc,argv);output=o.output;
        const std::uint16_t one=1;need(*reinterpret_cast<const unsigned char*>(&one)==1,"Existing aligned contract requires little endian");
        need(fs::create_directory(output),"Output directory must be new");
        need(fs::space(output).available>=192ULL*1024*1024,"Insufficient free space for bounded original data and output");
        nb::Ingress ingress(o.config);
        std::array<nb::PcapStream,3> parsers;
        std::array<std::ofstream,3> raw;
        for(unsigned i=0;i<3;++i)raw[i].open(output/("rx"+std::to_string(i+1)+".pcap"),std::ios::binary);
        std::ofstream csi(output/"windows.piwcsi2",std::ios::binary),tokens(output/"tokens.f32",std::ios::binary),rows(output/"windows.jsonl");
        need(bool(csi)&&bool(tokens)&&bool(rows),"Cannot open local evidence");
        if(!o.model.empty())worker=std::make_unique<Worker>(o);
        Fd listener;listener.value=socket(AF_INET,SOCK_STREAM,0);need(listener.value>=0,"Listener socket failed");
        int reuse=1;need(setsockopt(listener.value,SOL_SOCKET,SO_REUSEADDR,&reuse,sizeof(reuse))==0,"Socket option failed");
        sockaddr_in bind{};bind.sin_family=AF_INET;bind.sin_port=htons(std::uint16_t(o.port));
        inet_pton(AF_INET,o.bind.c_str(),&bind.sin_addr);
        need(::bind(listener.value,reinterpret_cast<sockaddr*>(&bind),sizeof(bind))==0 && listen(listener.value,3)==0,"Owned listener bind failed");
        auto deadline=Clock::now()+std::chrono::seconds(o.seconds);
        std::array<Fd,3> clients;std::array<bool,3> connected{},ended{};
        std::size_t connections=0,windows=0,dropped=0;std::uint64_t first_window_ns=0;
        std::cout<<"{\"listening\":"<<json_string(o.bind)<<",\"port\":"<<o.port<<",\"pc_required\":false,\"inference\":"<<(worker?"true":"false")<<"}"<<std::endl;
        const auto emit=[&] {
            for(auto& w:ingress.take_ready()) {
                need(windows<150,"Finite window budget reached");auto stamp=now_ns();
                if(!first_window_ns){first_window_ns=stamp;std::cout<<"{\"first_window_emitted_before_eof\":true}"<<std::endl;}
                auto wire=nb::encode_piwcsi2(w,++windows,stamp);
                csi.write(reinterpret_cast<const char*>(wire.data()),std::streamsize(wire.size()));
                auto input=demo_v1::decode_aligned(wire);auto prepared=pose_v1::preprocess(input.csi);
                tokens.write(reinterpret_cast<const char*>(prepared.data()),sizeof(prepared));
                bool queued=!worker || worker->push(Job{windows,prepared});if(!queued)++dropped;
                rows<<"{\"frame\":"<<windows<<",\"slot\":"<<w.start_reference_slot<<",\"board_monotonic_ns\":"<<stamp
                    <<",\"inference_queue_drop\":"<<(queued?"false":"true")<<"}\n";
                need(bool(csi)&&bool(tokens)&&bool(rows),"Actual CSI/token save failed");
            }
        };
        while(std::count(ended.begin(),ended.end(),true)!=3) {
            need(Clock::now()<deadline,"Finite receive deadline reached; no automatic restart");if(worker)worker->check();
            std::array<pollfd,4> polls{};polls[0]={connections<3?listener.value:-1,POLLIN,0};
            for(unsigned i=0;i<3;++i)polls[i+1]={clients[i].value,POLLIN,0};
            int ready=poll(polls.data(),polls.size(),100);if(ready<0&&errno==EINTR)continue;need(ready>=0,"Receive poll failed");
            if(polls[0].revents&POLLIN) {
                sockaddr_in address{};socklen_t length=sizeof(address);Fd accepted;
                accepted.value=accept(listener.value,reinterpret_cast<sockaddr*>(&address),&length);need(accepted.value>=0,"Accept failed");
                char ip[INET_ADDRSTRLEN]{};inet_ntop(AF_INET,&address.sin_addr,ip,sizeof(ip));
                auto found=std::find(o.peers.begin(),o.peers.end(),ip);need(found!=o.peers.end(),"Unexpected receiver peer");
                auto index=std::size_t(found-o.peers.begin());need(!connected[index],"Duplicate receiver connection; no automatic reconnect");
                clients[index].value=accepted.value;accepted.value=-1;connected[index]=true;++connections;
                if(connections==3){listener.close();std::cout<<"{\"receivers_ready\":true}"<<std::endl;}
            }
            for(unsigned i=0;i<3;++i)if(clients[i].value>=0 && (polls[i+1].revents&(POLLIN|POLLHUP|POLLERR))) {
                std::array<std::uint8_t,32768> buffer{};auto n=recv(clients[i].value,buffer.data(),buffer.size(),0);
                if(n<0 && errno==EINTR)continue;
                need(n>=0,"Router stream receive failed");
                if(n==0){parsers[i].finish();ended[i]=true;clients[i].close();continue;}
                raw[i].write(reinterpret_cast<const char*>(buffer.data()),n);need(bool(raw[i]),"Original PCAP save failed");
                for(auto& packet:parsers[i].append(buffer.data(),std::size_t(n))) {
                    ingress.feed(i,o.config.session_id,packet.timestamp_us,packet.port,packet.payload.data(),packet.payload.size());emit();
                }
            }
        }
        emit();auto batch=ingress.finish();need(windows==batch.windows.size(),"Incremental/batch window count differs");
        if(worker)worker->finish();
        csi.flush();tokens.flush();rows.flush();
        std::ofstream summary(output/"summary.json");
        summary<<"{\"windows\":"<<windows<<",\"enumerated\":"<<batch.decisions.size()<<",\"common_events\":"<<batch.common_events
            <<",\"first_window_board_monotonic_ns\":"<<first_window_ns<<",\"inferences\":"<<(worker?worker->completed():0)
            <<",\"inference_queue_drops\":"<<dropped<<",\"runtime_design_requires_pc\":false,\"hardware_acceptance_recorded\":false"
            <<",\"loopback_simulation\":"<<(o.simulation?"true":"false")
            <<",\"amplitude_profile_validated\":false,\"router_native_drop_counters_verified\":false,\"hdmi_tested\":false}\n";
        need(bool(summary),"Summary save failed");std::cout<<"{\"complete\":true,\"windows\":"<<windows<<"}"<<std::endl;return 0;
    } catch(const std::exception& error) {
        if(worker)worker->cancel();
        if(!output.empty()&&fs::is_directory(output)){std::ofstream out(output/"failure.json");out<<"{\"error\":"<<json_string(error.what())<<",\"automatic_retry\":false}\n";}
        std::cerr<<error.what()<<'\n';return 1;
    }
}
