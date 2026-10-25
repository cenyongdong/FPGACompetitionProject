#include "runtime.hpp"
#include "fixed_pool.hpp"
#include "handoff.hpp"
#include "wire.hpp"
#include "network.hpp"
#include "hdmi_output.hpp"
#include "hdmi_renderer.hpp"
#include "FPGA/hdmi_candidate/diagnostics/deferred_consume_r45/software/source/display/r9_startup_observer.hpp"
#include "r9_observer_mapping.hpp"
#include <atomic>
#include <csignal>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <thread>

namespace pp=pose180_pipeline;namespace dv=demo_v1;namespace fs=std::filesystem;
namespace {
volatile std::sig_atomic_t stop_requested=0;
void request_stop(int){stop_requested=1;}
void need(bool ok,const char* why){if(!ok)throw std::runtime_error(why);}
struct Input {pp::Window window;std::uint64_t arrived=0;};
struct Output {pp::Result result;std::uint64_t arrived=0,began=0,returned=0;std::uint32_t depth=0;bool complete=false;};
void save_unconfirmed(const fs::path& output,const Output& row){
    if(!row.complete)return;
    auto path=output/("unconfirmed-"+std::to_string(row.result.invocation)+".f32");
    if(fs::exists(path))return;
    std::ofstream stream(path,std::ios::binary);const auto& r=row.result;
    stream.write(reinterpret_cast<const char*>(r.input.data()),sizeof(r.input));
    stream.write(reinterpret_cast<const char*>(r.scores.data()),sizeof(r.scores));
    stream.write(reinterpret_cast<const char*>(r.poses.data()),sizeof(r.poses));stream.close();
    need(bool(stream),"Cannot preserve complete unconfirmed result");
}
}

int main(int argc,char** argv){
    if(argc!=7){std::cerr<<"package fresh-output frames session input-port hdmi(0|1)\n";return 2;}
    const fs::path package(argv[1]),output(argv[2]);
    const auto target=std::stoull(argv[3]),session=std::stoull(argv[4]);
    const auto port=std::stoul(argv[5]);const bool with_hdmi=std::string(argv[6])=="1";
    if(!target||target>54000||!session||!port||port>65535||
        (std::string(argv[6])!="0"&&std::string(argv[6])!="1"))return 2;
    std::signal(SIGTERM,request_stop);std::signal(SIGINT,request_stop);
    pp::FixedPool<Input,8> inputs;pp::FixedPool<Output,64> results;
    pp::Handoff<pp::Result> handoff;
    std::unique_ptr<pp::Runtime> runtime;std::unique_ptr<pose::hdmi::Output> display;
    dv::Socket listener,result_socket;std::atomic<int> input_fd{-1};
    std::thread receiver,publisher;
    std::atomic<std::size_t> received{0},archived{0},confirmed{0};std::size_t inferred=0,adopted=0;
    std::optional<pp::FixedPool<Output,64>::Lease> current,failed_publish;
    std::uint64_t pending_invocation=0;bool display_pending=false;
    bool owns_output=false;
    try{
        need(!fs::exists(output)&&fs::create_directory(output),"Fresh output directory required");owns_output=true;
        pp::Config config;config.graph=package/"models/piw24_pose180_ZG.json";
        config.raw=package/"models/piw24_pose180_ZG.raw";config.evidence=output/"engine";
        std::ofstream observer_log;std::unique_ptr<Mapping> mapping;
        std::string startup_mode;
        if(with_hdmi){
            std::ifstream mode(package/"startup-mode.txt");mode>>startup_mode;
            need(startup_mode=="healthy"||startup_mode=="consumed","Same-boot HDMI startup admission required");
            mapping=std::make_unique<Mapping>();observer_log.open(output/"startup-and-joint.jsonl");
            auto read=[&](unsigned o){return mapping->read(o);};auto write=[&](unsigned o,std::uint32_t v){mapping->write(o,v);};
            auto persist=[&](const std::string& line){observer_log<<line;observer_log.flush();need(bool(observer_log),"Observer evidence failed");};
            pose::r9_startup::Observer observer(read,write,persist);
            const auto before=observer.epoch("before_Engine",4,[]{std::this_thread::sleep_for(std::chrono::milliseconds(20));});
            need(startup_mode=="consumed"?pose::r9_startup::idle_after_drain(before,false):
                (pose::r9_startup::idle_healthy(before)&&before.words[4]==0),"Unhealthy pre-SDK HDMI state");
            config.on_device_ready=[&](const icraft::xrt::Device& device){
                display=std::make_unique<pose::hdmi::Output>(device,output/"hdmi.jsonl");display->verifyMemory();
            };
            const auto initialized=observer.epoch("Engine_Open_apply_memory",6,[&]{runtime=std::make_unique<pp::Runtime>(config);});
            need(pose::r9_startup::return_path_healthy(initialized),"Unhealthy initialization return path");
        }else runtime=std::make_unique<pp::Runtime>(config);
        std::cout<<"DEMO_ENGINE_INITIALIZED model=pose180 init_ms="<<runtime->init_ms()<<std::endl;
        result_socket.fd=::socket(AF_INET,SOCK_STREAM,0);need(result_socket.fd>=0,"Result socket failed");
        result_socket.timeout(15);dv::connect_result(result_socket.fd);
        publisher=std::thread([&]{
            std::optional<pp::FixedPool<Output,64>::Lease> active;
            try{
                std::array<unsigned char,pp::full_bytes> bytes{};std::uint64_t sequence=0;
                for(;;){
                    bool eof=false;active=results.pop(std::chrono::milliseconds(50),eof);
                    if(!active){if(eof)break;continue;}
                    const auto& row=active->value();const auto& r=row.result;++sequence;
                    pp::encode_full(bytes,r,session,sequence,row.arrived,row.began,row.returned,dv::now_ns(),row.depth);
                    dv::send_exact(result_socket.fd,bytes.data(),bytes.size());
                    std::array<unsigned char,8> ack{};dv::read_exact(result_socket.fd,ack.data(),ack.size());
                    need(pp::get64(ack.data())==sequence,"Host archive ACK differs");++archived;
                    // The full first result has been archived before these checks.
                    need(r.finite_outputs&&r.best_index<180,"Non-finite/invalid full result; first values retained");
                    need(r.invocation+1==sequence&&r.frame_id==1000000+r.invocation,"Output invocation identity differs");
                    if(with_hdmi)handoff.submit(r);
                    dv::send_exact(result_socket.fd,ack.data(),ack.size());++confirmed;active.reset();
                }
                ::shutdown(result_socket.fd,SHUT_WR);
            }catch(...){failed_publish=std::move(active);auto e=std::current_exception();
                handoff.fail(e);results.fail(e);inputs.fail(e);
                int fd=input_fd.load();if(fd>=0)::shutdown(fd,SHUT_RDWR);
            }
        });
        listener.fd=::socket(AF_INET,SOCK_STREAM,0);need(listener.fd>=0,"Input socket failed");dv::listen_on(listener.fd,static_cast<std::uint16_t>(port));
        receiver=std::thread([&]{
            try{
                dv::Socket client(::accept(listener.fd,nullptr,nullptr));client.timeout(15);input_fd=client.fd;
                std::array<unsigned char,pp::input_bytes> bytes{};std::uint64_t last_frame=0;
                for(std::size_t i=0;i<target;++i){
                    auto slot=inputs.acquire(std::chrono::milliseconds(1000));
                    dv::read_exact(client.fd,bytes.data(),bytes.size());
                    auto& row=slot.value();row.arrived=dv::now_ns();pp::decode_input(bytes,row.window);
                    need(row.window.frame_id>last_frame&&row.window.source_time_ns,"Input identity/order invalid");
                    last_frame=row.window.frame_id;inputs.publish(std::move(slot));++received;
                }
                unsigned char extra;need(::recv(client.fd,&extra,1,0)==0,"Unexpected input after target or no EOF");
                input_fd=-1;inputs.close();
            }catch(...){input_fd=-1;auto e=std::current_exception();inputs.fail(e);results.fail(e);handoff.fail(e);result_socket.stop();}
        });
        std::cout<<"DEMO_INPUT_READY port="<<port<<" frames="<<target<<std::endl;
        pose::hdmi::PreparedBackground canvas;
        if(with_hdmi)canvas.rgb565.resize(pose::hdmi::frameBytes);
        auto drain_display=[&]{
            while(display_pending){
                need(!stop_requested,"Requested bounded stop");results.check();
                if(display->poll_show()){handoff.complete(pending_invocation);display_pending=false;++adopted;}
                else std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        };
        auto run_loop=[&]{
            while(inferred<target){
                // A blocking forward may take seconds. Prove prior adoption
                // before entering it; never renew the 200ms deadline afterwards.
                drain_display();need(!stop_requested,"Requested bounded stop");results.check();
                bool eof=false;auto item=inputs.pop(std::chrono::milliseconds(10),eof);
                if(!item){need(!eof,"Input EOF before target");continue;}
                need(dv::now_ns()-item->value().arrived<1000000000ull,"Board input frame age exceeded 1s");
                current.emplace(results.acquire(std::chrono::milliseconds(1000)));
                auto& row=current->value();row.complete=false;row.arrived=item->value().arrived;row.began=dv::now_ns();
                runtime->infer(item->value().window,row.result);row.returned=dv::now_ns();
                row.depth=static_cast<std::uint32_t>(inputs.high_water());row.complete=true;item.reset();
                const bool finite=row.result.finite_outputs;const auto invocation=row.result.invocation;
                results.publish(std::move(*current));current.reset();++inferred;
                if(with_hdmi){
                    // Keep canvas capacity while overlapping only CPU background
                    // preparation with archive IO; no concurrent SDK calls.
                    pose::hdmi::prepare_background(canvas);
                    const auto& r=handoff.take();need(r.invocation==invocation,"Display handoff order differs");
                    auto rendered=pose::hdmi::render(std::move(canvas),r.scores.data(),r.poses.data(),180,r.frame_id);
                    display->begin_show(rendered.rgb565,static_cast<std::uint32_t>(r.frame_id));
                    canvas.rgb565=std::move(rendered.rgb565);pending_invocation=invocation;display_pending=true;
                }
                // A nonfinite result must finish its archive/error handoff before
                // any next SDK invocation; publisher's first error is authoritative.
                if(!finite){while(true){results.check();std::this_thread::sleep_for(std::chrono::milliseconds(1));}}
                if(inferred%300==0||inferred==target)std::cout<<"DEMO_PROGRESS inferred="<<inferred<<" confirmed="<<confirmed<<" received="<<received<<std::endl;
            }
            drain_display();receiver.join();inputs.check();results.close();publisher.join();results.check();
        };
        if(with_hdmi){
            auto read=[&](unsigned o){return mapping->read(o);};auto write=[&](unsigned o,std::uint32_t v){mapping->write(o,v);};
            auto persist=[&](const std::string& line){observer_log<<line;observer_log.flush();need(bool(observer_log),"Observer evidence failed");};
            pose::r9_startup::Observer observer(read,write,persist);const auto joint=observer.epoch("POSE180_HDMI",8,run_loop);
            need(pose::r9_startup::return_path_healthy(joint),"Joint return path changed");
            if(startup_mode=="consumed")
                need(pose::r9_startup::bounded_drain_quiet(joint,true),"Consumed startup terminal changed");
            else need((joint.words[4]&7)==5&&((joint.words[4]>>3)&511)==0&&
                !(joint.words[4]&0x0c000000u),"Untouched healthy consumer changed");
            need(joint.words[0]==pose::r9_startup::abi&&joint.words[3]==0,"Joint ABI/reset history changed");
            for(unsigned c=0;c<6;++c){const unsigned at=8+16*c;
                need(joint.words[at+2]==joint.words[at]&&joint.words[at+1]==joint.words[at+15]&&
                    joint.words[at+3]==0&&!(joint.words[at+12]&(1u<<31)),"Joint beat/burst/sticky error");
                need(joint.words[at]>0&&joint.words[at+1]>0,"Missing AI/HDMI path activity");
            }
            for(unsigned key:{0u,1u,2u})need(joint.words[88+key]==std::uint32_t(joint.words[40+key]+joint.words[72+key]),
                "HP2 branch conservation failed modulo 2^32");
            display->close();display.reset();
        }else run_loop();
        need(received==target&&inferred==target&&archived==target&&confirmed==target,"Incomplete end-to-end counters");
        runtime.reset();std::ofstream summary(output/"summary.json");
        summary<<"{\"model\":\"pose180\",\"completed\":"<<confirmed<<",\"received\":"<<received
            <<",\"host_archived\":"<<archived<<",\"inferred\":"<<inferred<<",\"HDMI_adopted\":"<<adopted
            <<",\"input_queue_high\":"<<inputs.high_water()<<",\"output_queue_high\":"<<results.high_water()
            <<",\"fixed_input_slots\":8,\"fixed_result_slots\":64,\"CSI_live\":false,\"engine_destroyed\":true}\n";
        need(bool(summary),"Final summary write failed");return 0;
    }catch(const std::exception& error){
        std::cerr<<"DEMO_STOP "<<error.what()<<std::endl;auto e=std::current_exception();
        handoff.fail(e);inputs.fail(e);results.fail(e);listener.stop();result_socket.stop();
        int fd=input_fd.load();if(fd>=0)::shutdown(fd,SHUT_RDWR);
        if(receiver.joinable())receiver.join();
        if(publisher.joinable())publisher.join();
        if(owns_output){
            try{if(current)save_unconfirmed(output,current->value());if(failed_publish)save_unconfirmed(output,failed_publish->value());
                results.save_queued([&](const Output& row){save_unconfirmed(output,row);});}catch(const std::exception& capture){std::cerr<<"EVIDENCE_ERROR "<<capture.what()<<std::endl;}
            std::ofstream failure(output/"failure.txt");failure<<error.what()<<"\ninferred="<<inferred<<" archived="<<archived<<" confirmed="<<confirmed<<" adopted="<<adopted<<"\n";
        }
        // Output destructor withholds release/_Exit if STOP cannot be proved.
        display.reset();runtime.reset();return 1;
    }
}
