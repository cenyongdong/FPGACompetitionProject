#include "adaptive_ingress.hpp"
#include "pcap_stream.hpp"
#include <algorithm>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>

using namespace nexmon_board;
namespace {
void require(bool v,const char* s){if(!v)throw std::runtime_error(s);}
std::vector<Datagram> read(const std::string& path) {
    std::ifstream f(path,std::ios::binary);require(bool(f),"Cannot read capture");
    PcapStream parser(true);std::vector<Datagram> result;std::array<std::uint8_t,8192> b{};
    while(f) {
        f.read(reinterpret_cast<char*>(b.data()),b.size());
        auto packets=parser.append(b.data(),std::size_t(f.gcount()));
        for(auto& p:packets)result.push_back(std::move(p));
    }
    parser.finish();require(!result.empty(),"Capture has no CSI records");return result;
}
}
int main(int argc,char** argv) {
    try {
        AdaptiveConfig c;c.source.streaming=true;c.source.session_id="offline-recording";
        c.source.receiver_ids={"rx1","rx2","rx3"};c.source.gains={1,1,1};
        std::array<std::string,3> pcaps;std::string report,ledger,output;
        for(int i=1;i<argc;++i) {
            const std::string flag=argv[i];auto next=[&](){require(i+1<argc,"Missing option value");return std::string(argv[++i]);};
            if(flag=="--source-mac") {
                const auto mac=next();require(mac.size()==17,"Bad MAC length");
                for(std::size_t r=0;r<6;++r)c.source.transmitter_mac[r]=std::uint8_t(std::stoul(mac.substr(3*r,2),nullptr,16));
            }else if(flag=="--channel")c.source.chanspec=std::uint16_t(std::stoul(next(),nullptr,0));
            else if(flag=="--pcaps")for(auto& p:pcaps)p=next();
            else if(flag=="--report")report=next();
            else if(flag=="--ledger")ledger=next();
            else if(flag=="--output")output=next();
            else if(flag=="--max-skew-us")c.max_skew_us=std::stoll(next());
            else if(flag=="--max-sequence-skew")c.max_sequence_skew=unsigned(std::stoul(next()));
            else throw std::runtime_error("Unknown option: "+flag);
        }
        require(!report.empty()&&!ledger.empty(),"Explicit report and ledger required");
        require(pcaps[0]!=pcaps[1]&&pcaps[1]!=pcaps[2]&&pcaps[0]!=pcaps[2],"Independent captures required");
        for(const auto& p:{report,ledger,output})if(!p.empty()){std::ifstream old(p);require(!old,"Refusing to overwrite replay output");}
        std::ofstream j(report),l(ledger),wire;if(!output.empty())wire.open(output,std::ios::binary);
        require(bool(j)&&bool(l)&&(output.empty()||bool(wire)),"Cannot create replay outputs");
        std::array<std::vector<Datagram>,3> packets;
        std::array<std::size_t,3> pos{};std::array<std::int64_t,3> origins{};
        for(std::size_t r=0;r<3;++r){packets[r]=read(pcaps[r]);origins[r]=packets[r].front().timestamp_us;}
        AdaptiveIngress in(c);std::int64_t observed=0,last_time=0,max_gap=0,first_time=-1;
        std::uint64_t count=0,approximate=0;std::array<std::int64_t,3> low{0,0,0},high{};
        auto consume=[&]() {
            for(const auto& w:in.take_ready()) {
                ++count;approximate+=bool(w.approximate_points);
                const auto time=std::int64_t(w.window.source_time_ns/1000);
                if(last_time)max_gap=std::max(max_gap,time-last_time);
                last_time=time;if(first_time<0)first_time=observed;
                for(std::size_t r=1;r<3;++r)if(w.tolerance_us[r]){
                    low[r]=low[r]?std::min(low[r],w.tolerance_us[r]):w.tolerance_us[r];high[r]=std::max(high[r],w.tolerance_us[r]);
                }
                l<<"{\"frame\":"<<count<<",\"observed_us\":"<<observed<<",\"alignment_version\":"<<w.alignment_version
                 <<",\"approximate_points\":"<<w.approximate_points<<",\"max_skew_us\":"<<w.max_skew_us<<",\"span_us\":"<<w.span_us
                 <<",\"tolerance_us\":[0,"<<w.tolerance_us[1]<<','<<w.tolerance_us[2]<<"],\"sequences\":[";
                for(std::size_t r=0;r<3;++r){if(r)l<<',';l<<'[';for(std::size_t t=0;t<20;++t){if(t)l<<',';l<<w.sequences[r][t];}l<<']';}l<<"]}\n";
                if(wire.is_open()){const auto bytes=encode_piwcsi2(w.window,count,w.window.source_time_ns);wire.write(reinterpret_cast<const char*>(bytes.data()),bytes.size());}
            }
        };
        // Capture wall clocks are NOT compared across devices. Relative file
        // starts only schedule this replay; sequence identities establish RF
        // association. No live pacing/transport latency claim is made here.
        for(;;) {
            std::size_t r=3;std::int64_t earliest=0;
            for(std::size_t peer=0;peer<3;++peer)if(pos[peer]<packets[peer].size()) {
                const auto t=packets[peer][pos[peer]].timestamp_us-origins[peer];
                if(r==3||t<earliest){r=peer;earliest=t;}
            }
            if(r==3)break;
            observed=std::max(observed,earliest);const auto& p=packets[r][pos[r]++];
            in.feed(r,c.source.session_id,p.timestamp_us,p.port,p.payload.data(),p.payload.size(),observed);consume();
        }
        in.poll(observed+30000);consume();const auto d=in.diagnostics();
        j<<"{\"offline_only\":true,\"CSI_live\":false,\"SDK\":false,\"model_accuracy_verified\":false,\"relative_capture_start_scheduler\":true"
         <<",\"windows\":"<<count<<",\"exact_event_windows\":"<<d.exact_windows<<",\"approximate_windows\":"<<approximate
         <<",\"approximate_points\":"<<d.approximate_points<<",\"skipped_points\":"<<d.skipped_points
         <<",\"max_source_gap_us\":"<<max_gap<<",\"first_replay_window_us\":"<<first_time
         <<",\"switches\":"<<d.switches<<",\"shadow_fits\":"<<d.shadow_fits<<",\"shadow_rejected\":"<<d.shadow_rejected
         <<",\"decoder_resets\":["<<d.decoder_resets[0]<<','<<d.decoder_resets[1]<<','<<d.decoder_resets[2]
         <<"],\"learned_min_us\":[0,"<<low[1]<<','<<low[2]<<"],\"learned_max_us\":[0,"<<high[1]<<','<<high[2]
         <<"],\"max_skew_cap_us\":"<<c.max_skew_us<<",\"max_sequence_skew\":"<<c.max_sequence_skew<<"}\n";
        require(bool(j)&&bool(l),"Replay metadata write failed");std::cout<<"offline windows="<<count<<" approximate="<<approximate<<" max_source_gap_us="<<max_gap<<'\n';return 0;
    }catch(const std::exception& e){std::cerr<<"Adaptive replay rejected: "<<e.what()<<'\n';return 1;}
}
