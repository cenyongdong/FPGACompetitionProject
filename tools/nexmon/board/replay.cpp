#include "ingress.hpp"
#include <algorithm>
#include <array>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using namespace nexmon_board;
struct Packet {std::int64_t stamp;std::uint16_t port;std::vector<std::uint8_t> payload;};
std::uint32_t le32(const std::uint8_t*p){return p[0]|std::uint32_t(p[1])<<8|std::uint32_t(p[2])<<16|std::uint32_t(p[3])<<24;}
std::uint16_t be16(const std::uint8_t*p){return std::uint16_t(std::uint16_t(p[0])<<8|p[1]);}
void check(bool ok,const char*reason){if(!ok)throw std::runtime_error(reason);}
std::vector<Packet> read_pcap(const std::string&path) {
    std::ifstream f(path,std::ios::binary);check(bool(f),"Cannot open PCAP");
    f.seekg(0,std::ios::end);auto size=f.tellg();check(size>=24&&size<=32*1024*1024,"PCAP byte budget/header failed");f.seekg(0);
    std::array<std::uint8_t,24> header{};f.read(reinterpret_cast<char*>(header.data()),24);
    check(le32(header.data())==0xa1b2c3d4&&le32(header.data()+20)==1,"Require little-endian microsecond Ethernet PCAP");
    std::vector<Packet> out;std::size_t records=0;
    while(f.peek()!=std::char_traits<char>::eof()) {
        std::array<std::uint8_t,16> h{};f.read(reinterpret_cast<char*>(h.data()),16);check(f.gcount()==16,"Truncated PCAP record header");
        auto n=le32(h.data()+8);check(n==le32(h.data()+12)&&n>=14&&n<=65535,"Truncated/oversized PCAP packet");
        check(++records<=40000,"PCAP record budget exceeded");
        std::vector<std::uint8_t>b(n);f.read(reinterpret_cast<char*>(b.data()),n);check(std::size_t(f.gcount())==n,"Truncated PCAP record");
        std::size_t o=14;auto kind=be16(b.data()+12);
        while(kind==0x8100||kind==0x88a8){check(o+4<=b.size(),"Truncated VLAN");kind=be16(b.data()+o+2);o+=4;}
        if(kind!=0x800)continue;
        check(o+20<=b.size(),"Truncated IPv4");
        if(b[o+9]!=17)continue;
        auto ihl=std::size_t((b[o]&15)*4);check((b[o]>>4)==4&&ihl>=20&&o+ihl+8<=b.size(),"Bad IPv4/UDP header");
        check((be16(b.data()+o+6)&0x3fff)==0,"Fragmented IPv4 datagram unsupported");
        auto u=o+ihl;auto bytes=be16(b.data()+u+4);check(bytes>=8&&u+bytes<=b.size(),"Bad UDP payload length");
        auto port=be16(b.data()+u+2);if(port!=5500&&port!=5501)continue;
        auto us=le32(h.data()+4);check(us<1000000,"Invalid PCAP microsecond field");
        out.push_back({std::int64_t(le32(h.data()))*1000000+us,port,{b.begin()+std::ptrdiff_t(u+8),b.begin()+std::ptrdiff_t(u+bytes)}});
    }
    return out;
}
std::array<std::uint8_t,6> mac(const std::string&s) {
    std::array<std::uint8_t,6> out{};check(s.size()==17,"MAC must use six colon-separated octets");
    for(std::size_t i=0;i<6;++i){check(i==5||s[i*3+2]==':',"Malformed MAC separator");
        auto octet=s.substr(i*3,2);char*end=nullptr;auto x=std::strtoul(octet.c_str(),&end,16);
        check(end==octet.c_str()+2&&x<=255,"Malformed MAC octet");out[i]=std::uint8_t(x);}
    return out;
}
std::string escaped(const std::string&s) {std::string r="\"";for(char c:s){if(c=='\\'||c=='\"')r+='\\';check(static_cast<unsigned char>(c)>=32,"Control byte in label");r+=c;}return r+'\"';}
}
int main(int argc,char**argv) {
    try {
        Config config;config.receiver_ids={"rx1","rx2","rx3"};std::array<std::string,3>pcaps;
        std::string binary,report,interleave="roundrobin";bool gains=false;
        for(int i=1;i<argc;++i) {
            std::string flag=argv[i];
            auto next=[&](){check(i+1<argc,"Missing argument");return std::string(argv[++i]);};
            if(flag=="--session")config.session_id=next();
            else if(flag=="--source-mac")config.transmitter_mac=mac(next());
            else if(flag=="--channel") {auto x=std::stoul(next(),nullptr,0);check(x<=65535,"Chanspec outside uint16");config.chanspec=std::uint16_t(x);}
            else if(flag=="--expected-events")config.expected_events=std::stoul(next());
            else if(flag=="--gains") {for(auto&g:config.gains)g=std::stod(next());gains=true;}
            else if(flag=="--receiver-ids")for(auto&s:config.receiver_ids)s=next();
            else if(flag=="--pcaps")for(auto&s:pcaps)s=next();
            else if(flag=="--output")binary=next();
            else if(flag=="--report")report=next();
            else if(flag=="--interleave")interleave=next();
            else throw std::runtime_error("Unknown argument: "+flag);
        }
        check(gains&&!binary.empty()&&!report.empty(),"Explicit --gains, --output and --report required; gains are candidate configuration, not RF calibration");
        check(interleave=="roundrobin"||interleave=="serial"||interleave=="chunked","Unknown interleave");
        check(pcaps[0]!=pcaps[1]&&pcaps[1]!=pcaps[2]&&pcaps[0]!=pcaps[2],"Independent receiver captures required");
        {std::ifstream a(binary),b(report);check(!a&&!b,"Refusing to overwrite replay output");}
        std::array<std::vector<Packet>,3> packets;
        for(std::size_t r=0;r<3;++r)packets[r]=read_pcap(pcaps[r]);
        Ingress ingress(config);std::array<std::size_t,3>pos{};std::size_t total=0,processed=0,emitted=0,first_ready=0;
        for(const auto&v:packets)total+=v.size();
        std::ofstream out(binary,std::ios::binary);check(bool(out),"Cannot create wire output");
        auto feed=[&](std::size_t r){const auto&p=packets[r][pos[r]++];ingress.feed(r,config.session_id,p.stamp,p.port,p.payload.data(),p.payload.size());++processed;
            auto windows=ingress.take_ready();if(!windows.empty()&&!first_ready)first_ready=processed;
            for(const auto&w:windows){auto wire=encode_piwcsi2(w,++emitted,0);out.write(reinterpret_cast<const char*>(wire.data()),std::streamsize(wire.size()));check(bool(out),"Wire output failed");}};
        if(interleave=="serial")for(std::size_t r=0;r<3;++r)while(pos[r]<packets[r].size())feed(r);
        else {const std::size_t chunk=interleave=="chunked"?97:1;
            while(processed<total)for(std::size_t r=0;r<3;++r)for(std::size_t j=0;j<chunk&&pos[r]<packets[r].size();++j)feed(r);}
        auto result=ingress.finish();check(emitted==result.windows.size(),"Incremental windows differ from final ledger");out.close();
        std::ofstream j(report);check(bool(j),"Cannot create JSON report");j<<std::setprecision(17);
        j<<"{\n\"session_id\":"<<escaped(config.session_id)<<",\n\"candidate_gains\":["<<config.gains[0]<<','<<config.gains[1]<<','<<config.gains[2]<<"],\n\"hardware_clock_proven\":false,\"physical_power_calibrated\":false,\"model_accuracy_verified\":false,\n";
        j<<"\"packets\":"<<total<<",\"first_ready_after_packets\":"<<first_ready<<",\"emitted_before_eof\":"<<(first_ready>0&&first_ready<total?"true":"false")<<",\n\"common_events\":"<<result.common_events<<",\"complete_windows\":"<<result.decisions.size()<<",\"valid_windows\":"<<result.windows.size()<<",\n\"slot_shifts\":["<<result.slot_shifts[0]<<','<<result.slot_shifts[1]<<','<<result.slot_shifts[2]<<"],\n\"nodes\":[";
        for(std::size_t r=0;r<3;++r){if(r)j<<',';const auto&n=result.nodes[r];j<<"{\"retained\":"<<n.retained<<",\"phase_scaled\":"<<n.phase_scaled<<",\"concentration\":"<<n.concentration<<",\"calibration_end_us\":"<<n.calibration_end_us<<",\"wraps\":"<<n.wraps<<",\"trailing_unpaired\":"<<(n.trailing_unpaired?"true":"false")<<",\"trailing_cores\":"<<n.trailing_cores<<'}';}
        j<<"],\n\"decisions\":[";
        for(std::size_t i=0;i<result.decisions.size();++i){if(i)j<<',';const auto&d=result.decisions[i];j<<"{\"start_reference_slot\":"<<d.start_reference_slot<<",\"valid\":"<<(d.valid?"true":"false")<<'}';}
        j<<"],\n\"windows\":[";
        for(std::size_t i=0;i<result.windows.size();++i){if(i)j<<',';const auto&w=result.windows[i];j<<"{\"start_reference_slot\":"<<w.start_reference_slot<<",\"event_indices\":[";
            for(std::size_t r=0;r<3;++r){if(r)j<<',';j<<'[';for(std::size_t t=0;t<20;++t){if(t)j<<',';j<<w.event_indices[r][t];}j<<']';}j<<"]}";}
        j<<"]\n}\n";check(bool(j),"JSON report failed");
        std::cout<<"valid="<<result.windows.size()<<" complete="<<result.decisions.size()<<" common="<<result.common_events<<" first_ready="<<first_ready<<'/'<<total<<'\n';
        return 0;
    }catch(const std::exception&e){std::cerr<<"ingress replay rejected: "<<e.what()<<'\n';return 1;}
}
