#include "csi.hpp"
#include "ingress.hpp"
#include "adaptive_ingress.hpp"
#include "pcap_stream.hpp"
#include <arpa/inet.h>
#include <sys/socket.h>
#include <poll.h>
#include <unistd.h>
#include <fstream>
#include <future>
#include <sstream>
#include <iomanip>
#include <map>
#include <set>

namespace pose180_demo {
namespace {
void need(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
struct Options {
    nexmon_board::Config config;
    nexmon_board::AdaptiveConfig adaptive_limits;
    bool adaptive=false;
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
    o.config.chanspec=std::stoul(take("channel"),nullptr,0);
    if(fields.count("alignment")) {
        const auto mode=take("alignment");need(mode=="strict"||mode=="adaptive","CSI alignment must be strict or adaptive");
        o.adaptive=mode=="adaptive";
    }
    if(o.adaptive) {
        if(fields.count("max_skew_us"))o.adaptive_limits.max_skew_us=std::stoll(take("max_skew_us"));
        if(fields.count("max_sequence_skew")) {
            const auto value=std::stoul(take("max_sequence_skew"));need(value<=3,"CSI sequence skew must be 0..3");
            o.adaptive_limits.max_sequence_skew=unsigned(value);
        }
    }
    need(fields.empty(),"Unknown CSI field");
    o.config.streaming=true;o.config.track_clock=true;
    o.config.session_id="configuration-check";
    if(o.adaptive){o.adaptive_limits.source=o.config;nexmon_board::AdaptiveIngress check(o.adaptive_limits);}
    else {nexmon_board::Ingress check(o.config);}
    return o;
}
}
Csi::Csi(Shared& s,const std::string& configuration,std::uint64_t session):shared_(s) {
    auto options=parse(configuration);std::promise<void> promise;auto ready=promise.get_future();
    thread_=std::thread([&,o=std::move(options),session,promise=std::move(promise)]() mutable {
        int listener=-1;std::array<int,3> clients{-1,-1,-1};bool announced=false;
        std::array<nexmon_board::PcapStream,3> parsers{nexmon_board::PcapStream(true),nexmon_board::PcapStream(true),nexmon_board::PcapStream(true)};
        std::array<std::uint64_t,3> last{},origin{};
        std::array<std::int64_t,3> capture_origin{},capture_watermark{},cutoff{};
        std::array<bool,3> silent{};
        std::unique_ptr<nexmon_board::Ingress> ingress;
        std::unique_ptr<nexmon_board::AdaptiveIngress> adaptive;
        std::array<std::uint64_t,3> reported_decoder_resets{};
        std::uint64_t epoch=session,frame=0,alignment_started=0,recovery_started=0,begin_after=0,last_good=0;
        std::uint64_t next_window_report=0;
        bool generation_ready=false;
        unsigned consecutive_failures=0;
        const auto started=now_ns();
        auto all_connected=[&]{return std::all_of(clients.begin(),clients.end(),[](int fd){return fd>=0;});};
        auto quote=[](const std::string& value){std::string out="\"";for(unsigned char c:value.substr(0,180)){
            if(c=='"'||c=='\\')out+='\\';
            if(c>=32)out+=char(c);}return out+'"';};
        auto report=[&](const char* phase,const char* scope,int receiver,const std::string& reason,
                        const nexmon_board::ContinuityDiagnostic* d=nullptr) {
            std::ostringstream out;
            out<<"{\"event\":\"csi_recovery\",\"phase\":"<<quote(phase)<<",\"scope\":"<<quote(scope)
               <<",\"rx\":"<<(receiver<0?0:receiver+1)<<",\"epoch\":"<<epoch
               <<",\"elapsed_ms\":"<<(now_ns()-started)/1000000<<",\"reason\":"<<quote(reason)
               <<",\"connected\":["<<(clients[0]>=0)<<','<<(clients[1]>=0)<<','<<(clients[2]>=0)<<']';
            if(d)out<<",\"arrival_us\":"<<d->arrival_us<<",\"previous_arrival_us\":"<<d->previous_arrival_us
                <<",\"host_delta_us\":"<<d->host_delta_us<<",\"tsf_delta_us\":"<<d->tsf_delta_us
                <<",\"counter_step\":"<<d->counter_step<<",\"sequence_before\":"<<d->sequence_before
                <<",\"sequence_after\":"<<d->sequence_after<<",\"have_previous\":"<<(d->have_previous?"true":"false")
                <<",\"event_clock_known\":"<<(d->event_clock_known?"true":"false")
                <<",\"tsf_before\":"<<d->tsf_before<<",\"tsf_after\":"<<d->tsf_after
                <<",\"counter_before\":"<<d->counter_before<<",\"counter_after\":"<<d->counter_after
                <<",\"phase_samples\":"<<d->phase_samples<<",\"phase_concentration\":"<<d->phase_concentration;
            if(std::string(phase)=="ready")out<<",\"alignment_ms\":"<<(now_ns()-alignment_started)/1000000
                <<",\"recovery_ms\":"<<s.stats.last_recovery_ms.load();
            out<<"}\n";s.stats.input_event(out.str());
        };
        auto report_windows=[&](const char* trigger) {
            if(adaptive) {
                const auto d=adaptive->diagnostics();std::ostringstream out;
                out<<"{\"event\":\"csi_adaptive\",\"trigger\":"<<quote(trigger)<<",\"epoch\":"<<epoch
                   <<",\"elapsed_ms\":"<<(now_ns()-started)/1000000<<",\"version\":"<<d.alignment_version
                   <<",\"exact_event_windows\":"<<d.exact_windows<<",\"approximate_windows\":"<<d.approximate_windows
                   <<",\"approximate_points\":"<<d.approximate_points<<",\"skipped_points\":"<<d.skipped_points
                   <<",\"expired_windows\":"<<d.expired_windows<<",\"ready_dropped\":"<<d.ready_dropped
                   <<",\"shadow_fits\":"<<d.shadow_fits<<",\"shadow_rejected\":"<<d.shadow_rejected
                   <<",\"switches\":"<<d.switches<<",\"partial_points\":"<<d.partial_points
                   <<",\"decoder_resets\":["<<d.decoder_resets[0]<<','<<d.decoder_resets[1]<<','<<d.decoder_resets[2]
                   <<"],\"tolerance_us\":["<<d.tolerance_us[0]<<','<<d.tolerance_us[1]<<','<<d.tolerance_us[2]
                   <<"],\"queued\":["<<d.queued_events[0]<<','<<d.queued_events[1]<<','<<d.queued_events[2]<<"]}\n";
                s.stats.input_event(out.str());next_window_report=now_ns()+5000000000ull;return;
            }
            if(!ingress)return;
            const auto d=ingress->diagnostics();const auto now=now_ns();
            std::ostringstream out;
            auto array=[&](const char* key,const auto& values){out<<",\""<<key<<"\":["<<values[0]<<','<<values[1]<<','<<values[2]<<']';};
            out<<"{\"event\":\"csi_windows\",\"trigger\":"<<quote(trigger)<<",\"epoch\":"<<epoch
               <<",\"elapsed_ms\":"<<(now-started)/1000000<<",\"no_window_ms\":"<<(now-last_good)/1000000
               <<",\"anchored\":"<<d.anchored<<",\"decided\":"<<d.decided<<",\"accepted\":"<<d.accepted
               <<",\"missing\":"<<d.missing<<",\"point_error\":"<<d.point_error<<",\"different_event\":"<<d.different_event
               <<",\"rejected_streak\":"<<d.rejected_streak<<",\"different_points\":"<<d.different_points
               <<",\"last_window_slot\":"<<d.last_window_slot<<",\"last_mismatch_slot\":"<<d.last_mismatch_slot;
            array("missing_points",d.missing_points);array("point_errors",d.point_errors);
            array("last_error_scaled",d.last_error_scaled);array("last_mismatch_sequences",d.last_mismatch_sequences);
            array("slot_shifts",d.slot_shifts);out<<"}\n";s.stats.input_event(out.str());
            for(unsigned r=0;r<3;++r) {
                const auto& n=d.nodes[r];std::ostringstream node;
                node<<std::fixed<<std::setprecision(4)<<"{\"event\":\"csi_node\",\"epoch\":"<<epoch<<",\"rx\":"<<r+1
                    <<",\"elapsed_ms\":"<<(now-started)/1000000<<",\"complete\":"<<n.complete_events
                    <<",\"retained\":"<<n.retained<<",\"invalid\":"<<n.invalid_events<<",\"retries\":"<<n.retransmissions
                    <<",\"wraps\":"<<n.wraps<<",\"locked\":"<<n.locked<<",\"phase_scaled\":"<<n.phase_scaled
                    <<",\"concentration\":"<<n.concentration
                    <<",\"phase_correction\":"<<n.phase_correction_scaled<<",\"phase_step\":"<<n.phase_step_scaled
                    <<",\"phase_residual\":"<<n.phase_residual_scaled<<",\"phase_updates\":"<<n.phase_updates
                    <<",\"phase_rejected\":"<<n.phase_rejected_blocks<<",\"phase_samples\":"<<n.phase_samples
                    <<"}\n";s.stats.input_event(node.str());
            }
            next_window_report=now+5000000000ull;
        };
        auto invalidate=[&](const char* scope,int r,const std::string& reason,
                            const nexmon_board::ContinuityDiagnostic* d=nullptr) {
            const auto now=now_ns();
            // Save the old generation's reasons before discarding its grid.
            report_windows("before_reset");
            if(!recovery_started)recovery_started=now;
            // Fence an inference already in flight before any reconnect/holdoff.
            s.stats.input_epoch=++epoch;
            ingress.reset();adaptive.reset();s.input.clear();s.stats.resynchronizing=true;s.stats.input_error(reason.c_str());
            ++s.stats.resyncs;
            if(std::string(scope)=="alignment")++s.stats.alignment_resets;else ++s.stats.transport_resets;
            // This bounds repeated bad alignment attempts without rejecting TCP.
            // Network retry/backoff belongs only to the RX guard.
            ++consecutive_failures;
            begin_after=now+(consecutive_failures>5?1000000000ull:consecutive_failures>2?250000000ull:0);
            report("reset",scope,r,reason,d);
        };
        auto close_receiver=[&](unsigned r,const std::string& reason) {
            if(clients[r]>=0)::close(clients[r]);
            clients[r]=-1;
            parsers[r]=nexmon_board::PcapStream(true);
            last[r]=origin[r]=0;capture_origin[r]=capture_watermark[r]=cutoff[r]=0;silent[r]=false;
            s.stats.input_connected=false;invalidate("transport",int(r),reason);
        };
        auto begin_alignment=[&] {
            // Fresh per-RX capture watermarks fence already queued history.
            // Parsers retain TCP framing; the new Ingress seeks a validated core0.
            const auto now=now_ns();
            for(unsigned r=0;r<3;++r)cutoff[r]=origin[r]?
                std::max(capture_watermark[r],capture_origin[r]+std::int64_t((now-origin[r])/1000)):capture_watermark[r];
            o.config.session_id=std::to_string(++epoch);s.stats.input_epoch=epoch;s.input.clear();
            if(o.adaptive){o.adaptive_limits.source=o.config;adaptive=std::make_unique<nexmon_board::AdaptiveIngress>(o.adaptive_limits);reported_decoder_resets={};}
            else ingress=std::make_unique<nexmon_board::Ingress>(o.config);
            alignment_started=last_good=now;s.stats.resynchronizing=true;
            generation_ready=false;next_window_report=now+5000000000ull;
            report("aligning","alignment",-1,"fresh_capture_watermarks");
        };
        auto publish=[&](const nexmon_board::JointWindow& window,const nexmon_board::AdaptiveWindow* quality=nullptr) {
            Input value;value.epoch=epoch;value.arrived=now_ns();value.window.frame_id=++frame;
            value.window.source_time_ns=window.source_time_ns;
            for(unsigned rx=0;rx<3;++rx)for(unsigned a=0;a<3;++a)for(unsigned t=0;t<20;++t)for(unsigned n=0;n<30;++n)
                value.window.csi[pose_v1::raw_index(rx,a,n,t)]=window.csi[((rx*3+a)*20+t)*30+n];
            if(quality) {
                std::ostringstream out;
                out<<"{\"event\":\"csi_adaptive_window\",\"epoch\":"<<epoch<<",\"frame\":"<<frame
                   <<",\"alignment_version\":"<<quality->alignment_version
                   <<",\"approximate_points\":"<<quality->approximate_points<<",\"max_skew_us\":"<<quality->max_skew_us
                   <<",\"span_us\":"<<quality->span_us<<",\"tolerance_us\":[0,"<<quality->tolerance_us[1]<<','<<quality->tolerance_us[2]
                   <<"],\"strict_grid_verified\":false}\n";
                s.stats.input_event(out.str());
            }
            if(s.stats.resynchronizing) {
                const auto elapsed=recovery_started?(now_ns()-recovery_started)/1000000:0;
                s.stats.last_recovery_ms=elapsed;s.stats.longest_recovery_ms=std::max(s.stats.longest_recovery_ms.load(),elapsed);
                report("ready","alignment",-1,"new_joint_window");recovery_started=0;consecutive_failures=0;
            }
            accept_input(s,value);last_good=now_ns();generation_ready=true;s.stats.resynchronizing=false;
        };
        try {
            listener=::socket(AF_INET,SOCK_STREAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);need(listener>=0,"CSI socket failed");
            int one=1;::setsockopt(listener,SOL_SOCKET,SO_REUSEADDR,&one,sizeof(one));sockaddr_in address{};
            address.sin_family=AF_INET;address.sin_port=htons(o.port);
            need(inet_pton(AF_INET,o.bind.c_str(),&address.sin_addr)==1,"CSI bind address invalid");
            need(!::bind(listener,reinterpret_cast<sockaddr*>(&address),sizeof(address))&&!::listen(listener,3),"CSI bind/listen failed");
            promise.set_value();announced=true;s.stats.input_epoch=epoch;s.stats.resynchronizing=true;
            std::array<unsigned char,16384> bytes{};
            while(!s.stop) {
                pollfd fds[]={{listener,POLLIN,0},{clients[0],POLLIN,0},{clients[1],POLLIN,0},{clients[2],POLLIN,0}};
                const auto polled=::poll(fds,4,20);if(polled<0){if(errno==EINTR)continue;throw std::runtime_error("CSI poll failed");}
                if(fds[0].revents&POLLIN) {
                    sockaddr_in peer{};socklen_t length=sizeof(peer);int fd=::accept4(listener,reinterpret_cast<sockaddr*>(&peer),&length,SOCK_NONBLOCK|SOCK_CLOEXEC);
                    if(fd>=0) {
                        char address_text[INET_ADDRSTRLEN];inet_ntop(AF_INET,&peer.sin_addr,address_text,sizeof(address_text));
                        auto it=std::find(o.peers.begin(),o.peers.end(),address_text);
                        if(it==o.peers.end()||clients[it-o.peers.begin()]>=0)::close(fd);
                        else {const auto r=it-o.peers.begin();clients[r]=fd;last[r]=now_ns();silent[r]=false;++s.stats.reconnects;
                              report("connected","transport",int(r),"accepted_without_board_backoff");}
                    }
                }
                s.stats.input_connected=all_connected();
                if(!ingress&&!adaptive&&all_connected()&&now_ns()>=begin_after)begin_alignment();
                for(unsigned r=0;r<3;++r) {
                    if(clients[r]<0)continue;
                    const auto idle=now_ns()-last[r];
                    if(idle>10000000000ull){close_receiver(r,"RX byte stream silent for ten seconds");continue;}
                    if(idle>2000000000ull&&!silent[r]){silent[r]=true;invalidate("alignment",int(r),"RX temporarily silent; retain TCP");}
                    // A descriptor accepted above was not part of this poll snapshot.
                    if(fds[r+1].fd!=clients[r]||!(fds[r+1].revents&(POLLIN|POLLHUP|POLLERR)))continue;
                    const auto count=::recv(clients[r],bytes.data(),bytes.size(),0);
                    if(count<0&&(errno==EAGAIN||errno==EINTR))continue;
                    if(count<=0){close_receiver(r,"RX disconnected");continue;}
                    last[r]=now_ns();silent[r]=false;
                    try {
                        for(const auto& packet:parsers[r].append(bytes.data(),count)) {
                            if(!origin[r]){origin[r]=now_ns();capture_origin[r]=packet.timestamp_us;}
                            need(!capture_watermark[r]||packet.timestamp_us>=capture_watermark[r],"RX capture clock moved backwards");
                            capture_watermark[r]=packet.timestamp_us;
                            const auto drift=std::int64_t(now_ns()-origin[r])-1000*(packet.timestamp_us-capture_origin[r]);
                            need(drift<500000000ll&&drift>-500000000ll,"RX capture age/drift exceeded; discard connection backlog");
                            if((!ingress&&!adaptive)||!all_connected()||packet.timestamp_us<=cutoff[r])continue;
                            if(adaptive) {
                                adaptive->feed(r,o.config.session_id,packet.timestamp_us,packet.port,packet.payload.data(),packet.payload.size(),std::int64_t(now_ns()/1000));
                                const auto diagnostic=adaptive->diagnostics();
                                if(diagnostic.decoder_resets!=reported_decoder_resets) {
                                    const auto& d=diagnostic.last_continuity;
                                    report("decoder_reset","decoder",int(d.receiver),nexmon_board::continuity_reason_name(d.reason),&d);
                                    reported_decoder_resets=diagnostic.decoder_resets;
                                }
                                for(const auto& w:adaptive->take_ready())publish(w.window,&w);
                            } else {
                                ingress->feed(r,o.config.session_id,packet.timestamp_us,packet.port,packet.payload.data(),packet.payload.size());
                                for(const auto& window:ingress->take_ready())publish(window);
                            }
                        }
                    }catch(const nexmon_board::ContinuityError& error) {
                        const auto& d=error.diagnostic();
                        invalidate("alignment",int(d.receiver),nexmon_board::continuity_reason_name(d.reason),&d);
                    }catch(const std::bad_alloc&) {throw;
                    }catch(const std::exception& error) {close_receiver(r,error.what());}
                }
                if(adaptive&&all_connected()) {
                    adaptive->poll(std::int64_t(now_ns()/1000));
                    for(const auto& w:adaptive->take_ready())publish(w.window,&w);
                    if(now_ns()>=next_window_report)report_windows("periodic");
                }
                if(ingress&&all_connected()) {
                    // Initial/recovery learning needs one full second of fresh
                    // events. A running generation should not retain a dead
                    // grid for ten seconds; reset only alignment, never TCP.
                    const auto timeout=generation_ready?2000000000ull:5000000000ull;
                    if(now_ns()-last_good>timeout)
                        invalidate("alignment",-1,generation_ready?"No jointly valid windows for two seconds":"Initial joint alignment exceeded five seconds");
                    else if(now_ns()>=next_window_report)report_windows("periodic");
                }
            }
        }catch(...){if(!announced)promise.set_exception(std::current_exception());else s.stats.isolated=true;}
        for(auto& fd:clients){if(fd>=0)::close(fd);fd=-1;}s.input.clear();s.stats.input_connected=false;
        if(listener>=0)::close(listener);
    });
    try{ready.get();}catch(...){thread_.join();throw;}
}
Csi::~Csi(){shared_.stop=true;if(thread_.joinable())thread_.join();}
}
