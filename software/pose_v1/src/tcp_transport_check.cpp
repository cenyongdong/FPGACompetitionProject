#include "tcp_receiver.hpp"
#include <cstring>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <thread>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <unistd.h>

using namespace pose_v1;using namespace pose_v1::transport;
static void need(bool b,const char* s){if(!b)throw std::runtime_error(s);}
static void put(std::vector<unsigned char>& b,size_t o,uint64_t v,size_t n){for(size_t i=0;i<n;++i)b[o+i]=(v>>(8*i))&255;}
static std::vector<unsigned char> encode(const Window& w){
    std::vector<unsigned char>b(record_bytes);std::memcpy(b.data(),"PIWCSI1\0",8);put(b,8,1,4);put(b,12,kPayloadBytes,4);put(b,16,w.frame_id,8);put(b,24,w.source_time_ns,8);
    for(size_t i=0;i<w.csi.size();++i){double re=w.csi[i].real(),im=w.csi[i].imag();uint64_t a,c;std::memcpy(&a,&re,8);std::memcpy(&c,&im,8);put(b,32+16*i,a,8);put(b,40+16*i,c,8);}return b;
}
static void self_test(){
    Window w;w.frame_id=42;w.source_time_ns=123;w.csi[0]={-0.0,1.25};auto b=encode(w);auto d=decode_record(b);need(encode(d)==b,"Raw bits changed");
    size_t refused=0;auto bad=[&](std::vector<unsigned char> x){try{decode_record(x);}catch(const std::exception&){++refused;return;}throw std::runtime_error("Invalid record accepted");};
    auto x=b;x[0]^=1;bad(x);x=b;x[8]=2;bad(x);x=b;x[12]^=1;bad(x);x=b;x.pop_back();bad(x);x=b;x.push_back(0);bad(x);x=b;put(x,32,0x7ff0000000000000ULL,8);bad(x);x=b;put(x,40,0x7ff8000000000000ULL,8);bad(x);
    LatestSlot slot;Item a;a.window=w;a.sequence=1;need(!slot.push(a),"Initial push dropped");a.sequence=2;need(slot.push(a),"Latest slot did not replace");auto popped=slot.pop(std::chrono::milliseconds(1));need(popped && popped->sequence==2,"Wrong latest item");
    a.sequence=3;slot.push(a);need(popped->sequence==2,"In-flight ownership changed");need(slot.clear(),"Reconnect clear missing");need(!slot.clear(),"Clear counted twice");slot.close();need(slot.finished()&&!slot.pop(std::chrono::milliseconds(1)),"Close failed");
    auto connect_to=[](uint16_t port){int fd=::socket(AF_INET,SOCK_STREAM,0);need(fd>=0,"Test socket");sockaddr_in a{};a.sin_family=AF_INET;a.sin_port=htons(port);inet_pton(AF_INET,"127.0.0.1",&a.sin_addr);need(::connect(fd,reinterpret_cast<sockaddr*>(&a),sizeof(a))==0,"Test connect");return fd;};
    auto send_all=[](int fd,const std::vector<unsigned char>&raw,size_t chunk){size_t sent=0;while(sent<raw.size()){size_t n=std::min(chunk,raw.size()-sent);auto count=::send(fd,raw.data()+sent,n,MSG_NOSIGNAL);need(count>0,"Test send");sent+=size_t(count);}};
    {Receiver rx("127.0.0.1",0,1000,1);int fd=connect_to(rx.port());send_all(fd,b,17);auto item=rx.pop(std::chrono::milliseconds(2000));need(item&&encode(item->window)==b,"Fragmented record changed");
        w.frame_id=43;auto second=encode(w);send_all(fd,second,second.size());item=rx.pop(std::chrono::milliseconds(2000));need(item&&encode(item->window)==second,"Second record changed");::shutdown(fd,SHUT_WR);::close(fd);
        rx.pop(std::chrono::milliseconds(2000));rx.check();auto s=rx.stats();need(rx.finished()&&s.received==2&&s.rejected==0&&s.overwritten==0,"Clean EOF statistics");}
    {Receiver rx("127.0.0.1",0,1000,1);int fd=connect_to(rx.port());std::vector<unsigned char> partial(b.begin(),b.begin()+100);send_all(fd,partial,13);::shutdown(fd,SHUT_WR);::close(fd);rx.pop(std::chrono::milliseconds(2000));rx.check();need(rx.finished()&&rx.stats().rejected==1&&rx.stats().received==0,"Partial record accepted");}
    {Receiver rx("127.0.0.1",0,1000,1);int fd=connect_to(rx.port());send_all(fd,b,b.size());need(bool(rx.pop(std::chrono::milliseconds(2000))),"Initial sequence record lost");send_all(fd,b,b.size());::shutdown(fd,SHUT_WR);::close(fd);rx.pop(std::chrono::milliseconds(2000));need(rx.finished()&&rx.stats().rejected==1&&rx.stats().received==1,"Duplicate frame accepted");}
    {Receiver rx("127.0.0.1",0,100,1);int fd=connect_to(rx.port());rx.pop(std::chrono::milliseconds(1000));need(rx.finished()&&rx.stats().rejected==1,"Idle connection not rejected");::close(fd);}
    need(refused==7,"Rejection coverage");std::cout<<"{\"self_test\":\"passed\",\"malformed_cases\":7,\"raw_bits\":true,\"bounded_slot\":true,\"loopback_fragmented\":true,\"partial_disconnect\":true,\"duplicate_rejected\":true,\"idle_timeout\":true}\n";
}
int main(int argc,char**argv){try{
    if(argc==2 && std::string(argv[1])=="--self-test"){self_test();return 0;}
    need(argc==7,"Usage: check OUTPUT PORT SESSIONS IDLE_MS CONSUMER_DELAY_MS ADDRESS");
    std::filesystem::path out=argv[1];need(!std::filesystem::exists(out),"Preserve transport output");std::filesystem::create_directory(out);
    int port=std::stoi(argv[2]),sessions=std::stoi(argv[3]),idle=std::stoi(argv[4]),delay=std::stoi(argv[5]);need(port>=0&&port<=65535&&sessions>0&&sessions<=8&&delay>=0&&delay<=2000,"Invalid transport limits");
    Receiver rx(argv[6],uint16_t(port),idle,size_t(sessions));std::cout<<"READY "<<rx.port()<<'\n'<<std::flush;
    std::ofstream index(out/"records.jsonl");size_t n=0;
    while(!rx.finished()){
        auto item=rx.pop(std::chrono::milliseconds(100));rx.check();if(!item)continue;
        auto b=encode(item->window);std::ofstream f(out/("record"+std::to_string(n)+".csi"),std::ios::binary);f.write(reinterpret_cast<const char*>(b.data()),b.size());need(bool(f),"Write raw record failed");
        index<<"{\"call\":"<<n++<<",\"frame_id\":"<<item->window.frame_id<<",\"session\":"<<item->session<<",\"sequence\":"<<item->sequence<<"}\n";
        if(delay)std::this_thread::sleep_for(std::chrono::milliseconds(delay));
    }
    rx.check();auto s=rx.stats();std::ofstream summary(out/"summary.json");summary<<"{\"sessions\":"<<s.sessions<<",\"received\":"<<s.received<<",\"rejected\":"<<s.rejected<<",\"overwritten\":"<<s.overwritten<<",\"reconnect_discarded\":"<<s.reconnect_discarded<<",\"consumed\":"<<n<<"}\n";
    need(bool(index)&&bool(summary),"Write transport summary failed");return 0;
}catch(const std::exception&e){std::cerr<<"STOP: "<<e.what()<<'\n';return 1;}}
