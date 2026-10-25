#include "csi.hpp"
#include "ingress.hpp"
#include "pcap_stream.hpp"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <poll.h>
#include <unistd.h>
#include <fstream>
#include <future>
#include <sstream>
#include <map>
#include <set>

namespace pose180_demo {
namespace {
void need(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
struct Options {
    nexmon_board::Config config;
    std::string bind;
    unsigned port=39033;
    std::array<std::string,3> peers;
};
Options parse(const std::string& path) {
    std::ifstream file(path);need(bool(file),"Cannot open CSI configuration");
    std::map<std::string,std::string> fields;std::string line;
    while(std::getline(file,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(line.empty()||line[0]=='#')continue;
        auto at=line.find('=');need(at!=std::string::npos,"Expected CSI key=value");
        need(fields.emplace(line.substr(0,at),line.substr(at+1)).second,"Repeated CSI key");
    }
    auto take=[&](const std::string& key){auto it=fields.find(key);need(it!=fields.end(),"Missing CSI field");auto v=it->second;fields.erase(it);return v;};
    Options o;o.bind=take("bind");o.port=std::stoul(take("port"));
    need(o.port>1023&&o.port<=65535,"CSI port invalid");
    for(unsigned r=0;r<3;++r){o.peers[r]=take("rx"+std::to_string(r+1));o.config.receiver_ids[r]=o.peers[r];o.config.gains[r]=std::stod(take("gain"+std::to_string(r+1)));}
    need(std::set<std::string>(o.peers.begin(),o.peers.end()).size()==3,"Distinct RX addresses required");
    auto source=take("source");need(source.size()==17,"TX MAC invalid");
    for(unsigned i=0;i<6;++i){std::size_t used=0;auto n=std::stoul(source.substr(i*3,2),&used,16);need(used==2&&n<=255&&(i==5||source[i*3+2]==':'),"TX MAC invalid");o.config.transmitter_mac[i]=std::uint8_t(n);}
    o.config.chanspec=std::stoul(take("channel"),nullptr,0);need(fields.empty(),"Unknown CSI field");
    o.config.streaming=true;o.config.session_id="configuration-check";nexmon_board::Ingress check(o.config);
    return o;
}
}
Csi::Csi(Shared& s,const std::string& configuration,std::uint64_t session):shared_(s) {
    auto options=parse(configuration);std::promise<void> promise;auto ready=promise.get_future();
    thread_=std::thread([&,o=std::move(options),session,promise=std::move(promise)]() mutable {
        int listener=-1;std::array<int,3> clients{-1,-1,-1};bool announced=false;
        auto close_clients=[&]{for(auto& fd:clients){if(fd>=0)::close(fd);fd=-1;}s.input.clear();s.stats.input_connected=false;};
        try {
            listener=::socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);need(listener>=0,"CSI socket failed");
            int one=1;::setsockopt(listener,SOL_SOCKET,SO_REUSEADDR,&one,sizeof(one));sockaddr_in address{};
            address.sin_family=AF_INET;address.sin_port=htons(o.port);
            need(inet_pton(AF_INET,o.bind.c_str(),&address.sin_addr)==1,"CSI bind address invalid");
            need(!::bind(listener,reinterpret_cast<sockaddr*>(&address),sizeof(address))&&!::listen(listener,3),"CSI bind/listen failed");
            promise.set_value();announced=true;
            std::uint64_t epoch=session,frame=0,retry_at=0;unsigned failures=0;
            auto make_ingress=[&]{o.config.session_id=std::to_string(++epoch);s.stats.input_epoch=epoch;s.stats.resynchronizing=true;
                return std::make_unique<nexmon_board::Ingress>(o.config);};
            auto ingress=make_ingress();
            std::array<nexmon_board::PcapStream,3> parsers{nexmon_board::PcapStream(true),nexmon_board::PcapStream(true),nexmon_board::PcapStream(true)};
            std::array<std::uint64_t,3> last{},origin{};std::array<std::int64_t,3> capture_origin{};
            std::array<unsigned char,16384> bytes{};auto last_good=now_ns();
            while(!s.stop) {
                pollfd fds[]={{listener,POLLIN,0},{clients[0],POLLIN,0},{clients[1],POLLIN,0},{clients[2],POLLIN,0}};
                ::poll(fds,4,20);
                try {
                    if(fds[0].revents&POLLIN) {
                        sockaddr_in peer{};socklen_t length=sizeof(peer);int fd=::accept4(listener,reinterpret_cast<sockaddr*>(&peer),&length,SOCK_NONBLOCK|SOCK_CLOEXEC);
                        if(fd>=0) {
                            char text[INET_ADDRSTRLEN];inet_ntop(AF_INET,&peer.sin_addr,text,sizeof(text));
                            auto it=std::find(o.peers.begin(),o.peers.end(),text);
                            if(now_ns()<retry_at||it==o.peers.end()||clients[it-o.peers.begin()]>=0)::close(fd);
                            else {const auto r=it-o.peers.begin();clients[r]=fd;last[r]=now_ns();++s.stats.reconnects;}
                        }
                    }
                    const bool connected=std::all_of(clients.begin(),clients.end(),[](int fd){return fd>=0;});
                    // SDK initialization or a disconnected source can take longer
                    // than this budget. Start it when all RX streams are present.
                    if(connected&&!s.stats.input_connected)last_good=now_ns();
                    s.stats.input_connected=connected;
                    for(unsigned r=0;r<3;++r) {
                        if(clients[r]<0)continue;
                        need(now_ns()-last[r]<2000000000ull,"RX stalled; flush all connection generations");
                        if(!(fds[r+1].revents&(POLLIN|POLLHUP|POLLERR)))continue;
                        auto count=::recv(clients[r],bytes.data(),bytes.size(),0);
                        if(count<0&&(errno==EAGAIN||errno==EINTR))continue;
                        need(count>0,"RX disconnected");last[r]=now_ns();
                        for(const auto& packet:parsers[r].append(bytes.data(),count)) {
                            if(!origin[r]){origin[r]=now_ns();capture_origin[r]=packet.timestamp_us;}
                            const auto drift=std::int64_t(now_ns()-origin[r])-1000*(packet.timestamp_us-capture_origin[r]);
                            need(drift<500000000ll&&drift>-500000000ll,"RX capture age/drift exceeded; discard backlog");
                            ingress->feed(r,o.config.session_id,packet.timestamp_us,packet.port,packet.payload.data(),packet.payload.size());
                            for(const auto& window:ingress->take_ready()) {
                                Input value;value.epoch=epoch;value.arrived=now_ns();value.window.frame_id=++frame;
                                // Source clock remains explicitly distinct from board monotonic time.
                                value.window.source_time_ns=window.source_time_ns;
                                for(unsigned rx=0;rx<3;++rx)for(unsigned a=0;a<3;++a)for(unsigned t=0;t<20;++t)for(unsigned n=0;n<30;++n)
                                    value.window.csi[pose_v1::raw_index(rx,a,n,t)]=window.csi[((rx*3+a)*20+t)*30+n];
                                accept_input(s,value);last_good=now_ns();failures=0;s.stats.resynchronizing=false;
                            }
                        }
                    }
                    if(s.stats.input_connected)need(now_ns()-last_good<10000000000ull,"No jointly valid windows; resync");
                }catch(const std::exception& error) {
                    s.stats.input_error(error.what());
                    ++s.stats.resyncs;close_clients();origin.fill(0);last.fill(0);capture_origin.fill(0);
                    for(auto& parser:parsers)parser=nexmon_board::PcapStream(true);
                    ingress=make_ingress();last_good=now_ns();
                    retry_at=now_ns()+std::min(30u,1u<<std::min(++failures,5u))*1000000000ull;
                }
            }
        }catch(...){if(!announced)promise.set_exception(std::current_exception());else s.stats.isolated=true;}
        close_clients();if(listener>=0)::close(listener);
    });
    try{ready.get();}catch(...){thread_.join();throw;}
}
Csi::~Csi(){shared_.stop=true;if(thread_.joinable())thread_.join();}
}
