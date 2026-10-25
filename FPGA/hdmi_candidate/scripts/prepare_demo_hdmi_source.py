from pathlib import Path
import shutil,json,hashlib
import argparse,subprocess
parser=argparse.ArgumentParser(description="Export the bounded demo_v1 + HDMI diagnostic; no board operations")
parser.add_argument('--project-root',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
O=args.project_root.resolve();C=Path(__file__).resolve().parents[3]
S=args.output.resolve();S.mkdir(parents=True,exist_ok=False)
for n in ('board','shared_fp16','output','diagnostics'):
 shutil.copytree(O/'demo_v1'/n,S/n)
shutil.copyfile(O/'demo_v1/CMakeLists.txt',S/'CMakeLists.txt')
H=S/'display';H.mkdir()
for n in ('hdmi_output.cpp','hdmi_output.hpp','hdmi_format.hpp','hdmi_canvas.cpp','hdmi_canvas.hpp','skeleton_render.cpp','skeleton_render.hpp'):
 shutil.copyfile(C/'software/core/display'/n,H/n)
# Reuse the previously verified full-memory-evidence diagnostic implementation.
p=H/'hdmi_output.cpp';s=p.read_text()
s=s.replace('std::ofstream log;','std::ofstream log;\n        std::filesystem::path evidence_dir;')
s=s.replace('p.log.open(evidence);','p.evidence_dir=evidence.parent_path();\n        p.log.open(evidence);')
s=s.replace('std::vector<uint8_t> source(frameBytes), actual(frameBytes);','''std::vector<uint8_t> source(frameBytes), actual(frameBytes);
        auto save=[&](const std::string& name,const std::vector<uint8_t>& data) {
            const auto path=p.evidence_dir/name;
            need(!std::filesystem::exists(path),"Fresh memory evidence required");
            std::ofstream file(path,std::ios::binary);
            file.write(reinterpret_cast<const char*>(data.data()),data.size());
            file.close();need(bool(file),"Cannot retain complete memory evidence");
        };''')
s=s.replace('p.frames[i].write(0, reinterpret_cast<char*>(source.data()), source.size());','save("memory-source-"+std::to_string(i)+".bin",source);\n            p.frames[i].write(0, reinterpret_cast<char*>(source.data()), source.size());')
s=s.replace('p.frames[i].read(reinterpret_cast<char*>(actual.data()), 0, actual.size());','''try {p.frames[i].read(reinterpret_cast<char*>(actual.data()),0,actual.size());}
            catch (...) {
                const auto original=std::current_exception();
                try {save("memory-partial-after-read-exception-"+std::to_string(i)+".bin",actual);}
                catch (...) {std::cerr<<"MEMORY_EXCEPTION_EVIDENCE_FAILED"<<std::endl;}
                std::rethrow_exception(original);
            }
            save("memory-actual-"+std::to_string(i)+".bin",actual);''')
p.write_text(s)

for n in ('r9_startup_observer.hpp','r9_observer_mapping.hpp','dma_probe_evidence.hpp'):
 shutil.copyfile(C/'FPGA/hdmi_candidate/software'/n,H/n)
p=S/'shared_fp16/application_core.hpp';s=p.read_text();s=s.replace('#include <string>','#include <string>\n#include <functional>\n#include <icraft-xrt/core/device.h>')
s=s.replace('size_t timing_frames = 0;','size_t timing_frames = 0;\n        std::function<void(const icraft::xrt::Device&)> on_device_ready;')
p.write_text(s)
p=S/'shared_fp16/application_core.cpp';s=p.read_text();s=s.replace('            initialization_ms = ms(begin);','            if(c.on_device_ready) c.on_device_ready(device);\n            initialization_ms = ms(begin);',1);p.write_text(s)
p=S/'CMakeLists.txt';s=p.read_text();s+='''
target_sources(pose_demo_v1 PRIVATE display/hdmi_output.cpp display/hdmi_canvas.cpp display/skeleton_render.cpp)
target_include_directories(pose_demo_v1 PRIVATE display)
''';p.write_text(s)
(S/'board/hdmi_handoff.hpp').write_text((C/'FPGA/hdmi_candidate/software/hdmi_handoff.hpp').read_text())
p=S/'board/main.cpp';s=p.read_text();s=s.replace('#include <thread>','#include <thread>\n#include "hdmi_handoff.hpp"\n#include "hdmi_output.hpp"\n#include "hdmi_canvas.hpp"\n#include "skeleton_render.hpp"\n#include "r9_startup_observer.hpp"\n#include "r9_observer_mapping.hpp"')
s=s.replace('    bool owns = false;','    bool owns = false;\n    HdmiHandoff hdmi_gate;\n    std::unique_ptr<pose::hdmi::Output> display;')
s=s.replace('        engine = std::make_unique<app::Engine>(config);','''        Mapping mapping;
        std::ofstream observer_log(output/"startup-and-joint.jsonl");
        auto read=[&](unsigned offset){return mapping.read(offset);};
        auto write=[&](unsigned offset,uint32_t value){mapping.write(offset,value);};
        auto persist=[&](const std::string& line){observer_log<<line;observer_log.flush();need(bool(observer_log),"Observer evidence failed");};
        pose::r9_startup::Observer observer(read,write,persist);
        const auto before=observer.epoch("before_Engine",2,[]{std::this_thread::sleep_for(std::chrono::milliseconds(20));});
        need(pose::r9_startup::idle_healthy(before),"Abnormal before Engine: no SDK start");
        config.on_device_ready=[&](const icraft::xrt::Device& device){
            display=std::make_unique<pose::hdmi::Output>(device,output/"hdmi.jsonl");display->verifyMemory();
        };
        const auto initialized=observer.epoch("Engine_Open_apply_memory",4,[&]{engine=std::make_unique<app::Engine>(config);});
        need(pose::r9_startup::return_path_healthy(initialized),"Abnormal Engine initialization return");
        std::ofstream hdmi_frames(output/"hdmi-frames.jsonl");
        const auto joint=observer.epoch("AI_HDMI",6,[&]{''')
s=s.replace('                    // 主机已保存，板端门检也已通过后，再允许主机展示该帧。','''                    // Complete Host archive and numeric gate precede the main-thread SDK display.
                    hdmi_gate.submit(r);
                    // 主机已保存，板端门检也已通过后，再允许主机展示该帧。''')
s=s.replace('                auto error = std::current_exception(); outgoing.fail(error); incoming.fail(error);','                auto error = std::current_exception(); hdmi_gate.fail(error); outgoing.fail(error); incoming.fail(error);')
anchor='            delivery.pressure(invocation,enqueue_begin,dv::now_ns(),depth);'
s=s.replace(anchor,anchor+'''
            const auto gated=hdmi_gate.take();need(gated.invocation==invocation,"Gated HDMI invocation mismatch");
            const auto draw_begin=dv::now_ns();
            auto rendered=pose_v1::render::draw(gated.scores,gated.poses,gated.frame_id);
            auto pixels=pose::hdmi::canvas(rendered.rgb);
            const auto show_begin=dv::now_ns();
            display->show(pixels,uint32_t(gated.frame_id));
            const auto show_end=dv::now_ns();
            if(gated.invocation==0 || gated.invocation+1==target){
                std::ofstream raw(output/("hdmi-"+std::to_string(gated.frame_id)+".rgb565"),std::ios::binary);
                raw.write(reinterpret_cast<const char*>(pixels.data()),pixels.size());raw.close();need(bool(raw),"Actual HDMI pixels not saved");
            }
            hdmi_frames<<"{\\"invocation\\":"<<gated.invocation<<",\\"frame\\":"<<gated.frame_id
                       <<",\\"top_index\\":"<<rendered.top_index<<",\\"render_canvas_ms\\":"<<double(show_begin-draw_begin)/1e6
                       <<",\\"show_ms\\":"<<double(show_end-show_begin)/1e6<<"}\\n";
            hdmi_frames.flush();need(bool(hdmi_frames),"HDMI frame evidence failed");
            hdmi_gate.complete(gated.invocation);
''',1)
s=s.replace('        delivery.save(output);save_diagnostics(engine.get(), output); engine.reset();','''        display->close();display.reset();
        });
        need(joint.words[3]==0,"Joint observer flags nonzero");
        for(unsigned c=0;c<6;++c)need(joint.words[11+16*c]==0,"Non-OKAY joint AXI response");
        for(unsigned c=0;c<6;++c)need(joint.words[8+16*c]>0 && joint.words[9+16*c]>0,"Missing AI/HDMI AXI activity");
        delivery.save(output);save_diagnostics(engine.get(),output);
        const auto closed=observer.epoch("Engine_Close",8,[&]{engine.reset();});
        need(pose::r9_startup::return_path_healthy(closed),"Abnormal Engine close return");''')
s=s.replace('auto failure = std::current_exception(); incoming.fail(failure); outgoing.fail(failure);','auto failure = std::current_exception(); hdmi_gate.fail(failure); incoming.fail(failure); outgoing.fail(failure);')
s=s.replace('        engine.reset(); return 1;','        if(display){display->close();display.reset();}\n        engine.reset(); return 1;')
p.write_text(s)
# Preserve original shared-source manifest; the only core overlay is the existing
# optional public Device callback, with its exact diff retained separately.
manifest=json.loads((O/'demo_v1/shared-source.json').read_text())
changed=[n for n,d in manifest['files'].items() if hashlib.sha256((S/'shared_fp16'/n).read_bytes()).hexdigest()!=d]
assert changed==['application_core.hpp','application_core.cpp'] or set(changed)=={'application_core.hpp','application_core.cpp'},changed
(S/'source-origin.json').write_text(json.dumps(dict(master=subprocess.check_output(['git','-C',str(O),'rev-parse','HEAD'],text=True).strip(),shared_overlay=changed,model_math_SDK_NPU_frame_protocol_changed=False,HDMI_four_HC_unchanged=True),indent=2))
print('Prepared latest demo_v1 + existing HDMI renderer, same-Device hook, gated main-thread handoff.')
