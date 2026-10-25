// 单Engine串行推理；网络与SDK隔离，所有输入和输出按拥有值交接。
#include "resident_support.hpp"
#include "aligned_csi.hpp"
#include "bounded_queue.hpp"
#include "network.hpp"
#include "delivery_timing.hpp"
#include "pose_frame.hpp"
#include <atomic>
#include <csignal>
#include <thread>
#include "hdmi_handoff.hpp"
#include "hdmi_output.hpp"
#include "hdmi_renderer.hpp"
#include "skeleton_render.hpp"
#include "r9_startup_observer.hpp"
#include "r9_observer_mapping.hpp"

namespace { volatile std::sig_atomic_t requested_stop=0; void request_stop(int){requested_stop=1;} }
namespace dv = demo_v1;
struct Input { pose_v1::Window window; uint64_t arrived = 0; size_t depth = 0; };
struct Output { app::Result value; uint64_t arrived = 0, began = 0, returned = 0; size_t depth = 0; int reference = -1; };
constexpr size_t full_bytes = 128 + 256 + 60400;
void save_emergency(const fs::path& root, const app::Result& r) {
    std::ofstream out(root / ("unpublished-" + std::to_string(r.invocation) + ".f32"), std::ios::binary);
    out.write(reinterpret_cast<const char*>(r.input.data()), sizeof(r.input));
    out.write(reinterpret_cast<const char*>(r.scores.data()), sizeof(r.scores));
    out.write(reinterpret_cast<const char*>(r.poses.data()), sizeof(r.poses));
    need(bool(out), "Emergency complete output save failed");
}

int main(int argc, char** argv) {
    if (argc != 6) { std::cerr << "package fresh-output frames session input-port\n"; return 2; }
    const fs::path package(argv[1]), output(argv[2]);
    const size_t target = std::stoull(argv[3]);
    const uint64_t session = std::stoull(argv[4]);
    const auto port_number = std::stoul(argv[5]);
    if (!target || target > 54000 || !session || !port_number || port_number > 65535) return 2;
    std::signal(SIGTERM,request_stop);std::signal(SIGINT,request_stop);
    dv::Queue<Input> incoming(8);
    dv::Queue<Output> outgoing(64);
    std::atomic<size_t> received{0}, sent{0}, archived{0}, reference_checks{0};
    std::thread receiver, publisher;
    std::unique_ptr<app::Engine> engine;
    dv::Socket listener, result_socket;
    std::atomic<int> input_fd{-1};
    size_t completed = 0;
    std::optional<Output> current, failed_publish;
    dv::DeliveryTiming delivery(64);
    std::vector<Case> cases;
    bool current_has_result = false;
    bool owns = false;
    HdmiHandoff hdmi_gate;
    std::unique_ptr<pose::hdmi::Output> display;
    try {
        need(!fs::exists(output) && fs::create_directory(output), "Fresh demo_v1 output required");
        owns = true; fs::create_directory(output / "engine");
        cases = load_cases(package);
        fc::configure(3); pose_v1::timing_sdk::configure(false);
        pose::failure_evidence::configure(output / "failed-host-inputs");
        pose::source_diagnostic::configure(output / "failed-host-inputs/source-readback");
        pose::stage_observation::configure(output / "copy-observations", {},
#ifdef DEMO_READ_DIAGNOSTIC
            UINT64_MAX
#else
            3
#endif
        );
        pose::producer_count::configure(output / "producer-counts");
        pose::tensor_identity::configure(output / "tensor-identities", 3);
        app::Config config;
        config.graph = package / "models/piw24_shared_ZG.json";
        config.raw = package / "models/piw24_shared_ZG.raw";
        config.evidence = output / "engine"; config.allow_device_init = true;
        config.minimal_log = true; config.diagnostic_frames = 0; config.timing_frames = 3;
        Mapping mapping;
        std::ofstream observer_log(output/"startup-and-joint.jsonl");
        auto read=[&](unsigned offset){return mapping.read(offset);};
        auto write=[&](unsigned offset,uint32_t value){mapping.write(offset,value);};
        auto persist=[&](const std::string& line){observer_log<<line;observer_log.flush();need(bool(observer_log),"Observer evidence failed");};
        pose::r9_startup::Observer observer(read,write,persist);
        std::ifstream startup_file(package/"startup-mode.txt");
        std::string startup_mode;startup_file>>startup_mode;
        need(startup_mode=="consumed" || startup_mode=="healthy", "Startup admission mode absent");
        const bool consumed_startup=startup_mode=="consumed";
        const auto before=observer.epoch("before_Engine",4,[]{std::this_thread::sleep_for(std::chrono::milliseconds(20));});
        need(consumed_startup ? pose::r9_startup::idle_after_drain(before,false) :
             (pose::r9_startup::idle_healthy(before) && before.words[4]==0),
             "Abnormal before Engine: no SDK start");
        config.on_device_ready=[&](const icraft::xrt::Device& device){
            display=std::make_unique<pose::hdmi::Output>(device,output/"hdmi.jsonl");display->verifyMemory();
        };
        const auto initialized=observer.epoch("Engine_Open_apply_memory",6,[&]{engine=std::make_unique<app::Engine>(config);});
        need(pose::r9_startup::return_path_healthy(initialized),"Abnormal Engine initialization return");
        std::ofstream hdmi_frames(output/"hdmi-frames.jsonl");
        const auto joint=observer.epoch("AI_HDMI",8,[&]{
        std::cout << "DEMO_ENGINE_INITIALIZED init_ms=" << engine->init_ms() << std::endl;
        result_socket.fd = ::socket(AF_INET, SOCK_STREAM, 0);
        need(result_socket.fd >= 0, "Output socket creation failed");
        result_socket.timeout(15); dv::connect_result(result_socket.fd);
        publisher = std::thread([&] {
            std::optional<Output> active;
            try {
                uint64_t sequence = 0;
                for (;;) {
                    active = outgoing.pop();
                    if (!active) break;
                    const auto& row = *active;
                    const auto& r = row.value;
                    auto& transport=delivery.begin(r.invocation,sequence+1,dv::now_ns());
                    pose::output::Frame frame;
                    frame.session = session; frame.frame = r.frame_id; frame.invocation = r.invocation;
                    frame.source_ns = r.source_time_ns; frame.published_ns = dv::now_ns();
                    frame.sequence = ++sequence; frame.flags = 0;
                    frame.candidate = uint32_t(r.best_index); frame.score = r.scores[r.best_index]; frame.joints = r.selected_pose;
                    const auto pose = pose::output::encode_for_archive(frame);
                    std::vector<unsigned char> bytes(full_bytes, 0);
                    std::memcpy(bytes.data(), "PIWFUL2\0", 8);
                    dv::put32(bytes.data() + 8, 2); dv::put32(bytes.data() + 12, full_bytes);
                    const uint64_t fields[] = {session, r.frame_id, r.invocation, r.source_time_ns,
                        row.arrived, row.began, row.returned, sequence};
                    for (size_t i = 0; i < 8; ++i) dv::put64(bytes.data() + 16 + i * 8, fields[i]);
                    const double timing[] = {r.process_ms, r.preprocess_ms, r.forward_ms, r.output_ms};
                    std::memcpy(bytes.data() + 80, timing, sizeof(timing));
                    dv::put32(bytes.data() + 112, uint32_t(row.depth));
                    dv::put32(bytes.data() + 120, uint32_t(r.best_index));
                    auto p = bytes.data() + 128;
                    std::memcpy(p, pose.data(), pose.size()); p += pose.size();
                    std::memcpy(p, r.input.data(), sizeof(r.input)); p += sizeof(r.input);
                    std::memcpy(p, r.scores.data(), sizeof(r.scores)); p += sizeof(r.scores);
                    std::memcpy(p, r.poses.data(), sizeof(r.poses));
                    transport.encode_end=dv::now_ns();transport.send_begin=dv::now_ns();
                    dv::send_exact(result_socket.fd, bytes.data(), bytes.size());
                    transport.send_end=dv::now_ns();
                    std::array<unsigned char, 8> acknowledgement{};
                    transport.ack_begin=dv::now_ns();
                    dv::read_exact(result_socket.fd, acknowledgement.data(), acknowledgement.size());
                    transport.ack_end=dv::now_ns();
                    need(dv::u64(acknowledgement.data()) == sequence, "Host archive acknowledgement differs");
                    ++archived;
                    bool finite = true;
                    for (auto x : r.scores) finite = finite && std::isfinite(x);
                    for (auto x : r.poses) finite = finite && std::isfinite(x);
                    need(finite && r.best_index < 100, "Non-finite/invalid result; complete actual already archived");
                    if (row.reference >= 0) {
                        const auto& reference = cases.at(size_t(row.reference));
                        const auto gate = pose::shared_output_gate::compare(r.scores, reference.scores, r.poses, reference.poses, 3.0, 0.2f);
                        need(gate.accepted, "Numeric gate failed; complete actual already archived; no retry");
                        ++reference_checks;
                    }
                    // Complete Host archive and numeric gate precede the main-thread SDK display.
                    hdmi_gate.submit(r);
                    // 主机已保存，板端门检也已通过后，再允许主机展示该帧。
                    transport.gate_end=dv::now_ns();
                    dv::send_exact(result_socket.fd, acknowledgement.data(), acknowledgement.size()); ++sent;
                    transport.confirm_end=dv::now_ns();delivery.done(transport);
                    active.reset();
                }
                ::shutdown(result_socket.fd, SHUT_WR);
            } catch (...) {
                failed_publish = std::move(active);
                auto error = std::current_exception(); hdmi_gate.fail(error); outgoing.fail(error); incoming.fail(error);
                int fd = input_fd.load(); if (fd >= 0) ::shutdown(fd, SHUT_RDWR);
            }
        });
        listener.fd = ::socket(AF_INET, SOCK_STREAM, 0); need(listener.fd >= 0, "Listener creation failed");
        dv::listen_on(listener.fd, uint16_t(port_number));
        receiver = std::thread([&] {
            try {
                dv::Socket client(accept(listener.fd, nullptr, nullptr)); client.timeout(15); input_fd = client.fd;
                uint64_t last_frame = 0;
                for (size_t i = 0; i < target; ++i) {
                    std::vector<unsigned char> bytes(dv::csi_record_bytes);
                    dv::read_exact(client.fd, bytes.data(), bytes.size());
                    Input row; row.arrived = dv::now_ns(); row.window = dv::decode_aligned(bytes);
                    need(row.window.frame_id > last_frame && row.window.source_time_ns > 0, "Invalid/reordered input frame");
                    last_frame = row.window.frame_id;
                    // 接收端单生产者，推理线程独占消费；不覆盖尚未处理的窗口。
                    incoming.wait_push(std::move(row),std::chrono::milliseconds(1000)); ++received;
                }
                unsigned char extra;
                need(recv(client.fd, &extra, 1, 0) == 0, "Unexpected extra CSI or missing input EOF");
                input_fd = -1; incoming.close();
            } catch (...) { input_fd = -1; incoming.fail(std::current_exception()); }
        });
        std::cout << "DEMO_INPUT_READY port=" << port_number << " frames=" << target << std::endl;
        while (auto item = incoming.pop()) {
            need(!requested_stop,"Requested bounded test stop");
            outgoing.check(); current.emplace(); current_has_result = false;
            auto& row = *current; row.arrived = item->arrived; row.began = dv::now_ns();
            const Case* reference = nullptr;
            for (size_t i = 0; i < cases.size(); ++i) {
                const auto& c = cases[i];
                if (std::memcmp(c.window.csi.data(), item->window.csi.data(), sizeof(item->window.csi)) == 0) {
                    reference = &c; row.reference = int(i);
                }
            }
            row.value = reference ? engine->process_window_checked(item->window, reference->name, reference->input)
                                  : engine->process_window(item->window);
            row.returned = dv::now_ns(); row.depth = incoming.high_water();
            current_has_result = true;
            const auto enqueue_begin=dv::now_ns();const auto invocation=row.value.invocation;
            size_t depth=0;
            try {depth=outgoing.wait_push(std::move(row),std::chrono::milliseconds(1000));}
            catch (...) {delivery.pressure(invocation,enqueue_begin,dv::now_ns(),outgoing.high_water());throw;}
            delivery.pressure(invocation,enqueue_begin,dv::now_ns(),depth);
            const auto gated=hdmi_gate.take();need(gated.invocation==invocation,"Gated HDMI invocation mismatch");
            const auto draw_begin=dv::now_ns();
            auto rendered=pose::hdmi::render(gated.scores,gated.poses,gated.frame_id);
            auto pixels=std::move(rendered.rgb565);
            const auto show_begin=dv::now_ns();
            display->show(pixels,uint32_t(gated.frame_id));
            const auto show_end=dv::now_ns();
            if(gated.invocation==0 || gated.invocation+1==target){
                std::ofstream raw(output/("hdmi-"+std::to_string(gated.frame_id)+".rgb565"),std::ios::binary);
                raw.write(reinterpret_cast<const char*>(pixels.data()),pixels.size());raw.close();need(bool(raw),"Actual HDMI pixels not saved");
            }
            hdmi_frames<<"{\"invocation\":"<<gated.invocation<<",\"frame\":"<<gated.frame_id
                       <<",\"top_index\":"<<rendered.top_index<<",\"render_rgb565_ms\":"<<double(show_begin-draw_begin)/1e6
                       <<",\"show_ms\":"<<double(show_end-show_begin)/1e6<<"}\n";
            hdmi_frames.flush();need(bool(hdmi_frames),"HDMI frame evidence failed");
            hdmi_gate.complete(gated.invocation);

            current.reset(); current_has_result = false; ++completed;
            if (completed % 300 == 0 || completed == target)
                std::cout << "DEMO_PROGRESS completed=" << completed << " received=" << received << " sent=" << sent << std::endl;
        }
        receiver.join(); incoming.check(); outgoing.close(); publisher.join(); outgoing.check();
        need(received == target && completed == target && sent == target && archived == target, "Incomplete demo counters");
        display->close();display.reset();
        });
        if(consumed_startup)
            need(pose::r9_startup::bounded_drain_quiet(joint,true),"Consumed startup terminal changed");
        else
            need((joint.words[4]&7)==5 && ((joint.words[4]>>3)&511)==0 &&
                 !(joint.words[4]&0x0c000000u), "Untouched healthy consumer changed");
        // Hardware counters naturally wrap. Preserve their original 32-bit values;
        // compare fixed-width invariants, never invent a 64-bit total.
        need(joint.words[0]==pose::r9_startup::abi && joint.words[3]==0,
             "Joint ABI/reset history changed");
        for(unsigned c=0;c<6;++c){const unsigned at=8+16*c;
            need(joint.words[at+2]==joint.words[at] && joint.words[at+1]==joint.words[at+15] &&
                 joint.words[at+3]==0 && !(joint.words[at+12]&(1u<<31)),
                 "Joint fixed-width burst/beat or sticky error contract failed");
        }
        for(unsigned key:{0u,1u,2u})
            need(joint.words[88+key]==uint32_t(joint.words[40+key]+joint.words[72+key]),
                 "HP2 branch conservation failed modulo 2^32");
        for(unsigned c=0;c<6;++c)need(joint.words[11+16*c]==0,"Non-OKAY joint AXI response");
        for(unsigned c=0;c<6;++c)need(joint.words[8+16*c]>0 && joint.words[9+16*c]>0,"Missing AI/HDMI AXI activity");
        delivery.save(output);save_diagnostics(engine.get(),output);
        const auto closed=observer.epoch("Engine_Close",10,[&]{engine.reset();});
        need(pose::r9_startup::return_path_healthy(closed),"Abnormal Engine close return");
        std::ofstream summary(output / "summary.json");
        summary << "{\"completed\":" << completed << ",\"host_archived\":" << archived << ",\"reference_checks\":" << reference_checks << ",\"received\":" << received
                << ",\"sent\":" << sent << ",\"input_queue_high\":" << incoming.high_water()
                << ",\"output_queue_high\":" << outgoing.high_water() << ",\"engine_destroyed\":true}\n";
        need(bool(summary), "Summary write failed"); return 0;
    } catch (const std::exception& error) {
        std::cerr << "DEMO_STOP " << error.what() << std::endl;
        auto failure = std::current_exception(); hdmi_gate.fail(failure); incoming.fail(failure); outgoing.fail(failure);
        listener.stop(); result_socket.stop(); int fd = input_fd.load(); if (fd >= 0) ::shutdown(fd, SHUT_RDWR);
        if (receiver.joinable()) receiver.join();
        if (publisher.joinable()) publisher.join();
        std::string diagnostic;
        if (owns) {
            try { delivery.save(output); } catch (const std::exception& e) { diagnostic = e.what(); }
            try {
                if (current && current_has_result) save_emergency(output, current->value);
                if (failed_publish) save_emergency(output, failed_publish->value);
                for (const auto& row : outgoing.drain_for_evidence()) save_emergency(output, row.value);
            } catch (const std::exception& e) { diagnostic = e.what(); }
            try { save_diagnostics(engine.get(), output); } catch (const std::exception& e) { diagnostic = e.what(); }
            std::ofstream out(output / "failure.json");
            out << "{\"error\":" << quote(error.what()) << ",\"diagnostic_error\":" << quote(diagnostic)
                << ",\"completed\":" << completed << ",\"host_archived\":" << archived << ",\"retry\":false}\n";
        }
        if(display){display->close();display.reset();}
        engine.reset(); return 1;
    }
}
