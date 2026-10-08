"""Isolated executable display process; old r2 modules stay frozen."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];src=root/'software/pose_v1'
entry=(src/'src/system_timing_check.cpp').read_text(encoding='utf-8')
entry=entry.replace('#include "system_timing.hpp"','#include "system_timing.hpp"\n#include "display_process.hpp"\n#include "display_queue.hpp"')
entry=entry.replace('host-check|measure-2hz|measure-5hz','host-check|process-three|measure-2hz|measure-5hz').replace('mode=="measure-2hz"||mode=="measure-5hz"','mode=="process-three"||mode=="measure-2hz"||mode=="measure-5hz"')
entry=entry.replace('auto cases=proof::fixtureWindows(package,true);cases.pop_back();','auto cases=proof::fixtureWindows(package,mode!="process-three");if(mode!="process-three")cases.pop_back();')
entry=entry.replace('    bool firstCapture=false;', '''    namespace display=pose::display;
    display::Queue poses;
    struct DisplayRecord {uint64_t invocation,frame,request,dispatch,begin,drawn,converted,received,published;};
    std::vector<DisplayRecord> displayRecords;displayRecords.reserve(33);
    std::unique_ptr<display::Process> displayProcess;
    bool firstCapture=false;''')
entry=entry.replace('abort=true;frames.fail(e);','abort=true;frames.fail(e);poses.fail(e);')
entry=entry.replace('std::thread network,encoder;','std::thread network,encoder,displayPump;')
needle='''    try{
        network=std::thread'''
replacement='''    try{
        // exec before VPU/NPU creation; child owns no SDK or device state.
        displayProcess=std::make_unique<display::Process>(fs::canonical(argv[0]).parent_path()/"pose_display_worker",out/"display");
        displayPump=std::thread([&]{try{
            while(auto pose=poses.next()){
                const auto dispatch=ns();auto image=displayProcess->render(*pose,[&]{return abort.load();});
                vv::OwnedFrame frame;frame.nv12=std::move(image.nv12);frame.sourceFrame=image.frame;frame.invocation=image.invocation;frame.generatedNs=image.convertEnd;
                frames.publish(std::move(frame));
                displayRecords.push_back({image.invocation,image.frame,pose->publishedNs,dispatch,image.renderBegin,image.drawEnd,image.convertEnd,image.receivedEnd,ns()});
            }
            displayProcess->finish();
        }catch(...){fail(std::current_exception());}});
        network=std::thread'''
assert needle in entry;entry=entry.replace(needle,replacement)
start=entry.index('            auto rgb=rr::draw(v.result.scores')
end=entry.index('\n        }\n        input.finish',start)
entry=entry[:start]+'''            display::Pose pose;pose.frame=v.result.frame_id;pose.invocation=v.result.invocation;pose.scores=v.result.scores;pose.poses=v.result.poses;pose.publishedNs=ns();poses.publish(std::move(pose));''' +entry[end:]
entry=entry.replace('input.finish(out,mode=="measure-2hz");','input.finish(out,mode!="measure-5hz",mode=="process-three"?4:33);\n        poses.close();')
entry=entry.replace('    if(encoder.joinable())encoder.join();','    if(displayPump.joinable())displayPump.join();\n    if(encoder.joinable())encoder.join();')
entry=entry.replace('''    // All large diagnostic writes''','''    auto displayLog=trace(out/"display-timing.jsonl");
    for(const auto& d:displayRecords){
        check(d.invocation<measured.size()&&measured[d.invocation].result.frame_id==d.frame,"Display timing ownership differs");
        auto& v=measured[d.invocation];v.drawEnd=d.drawn;v.convertEnd=d.converted;v.published=d.published;
        displayLog<<"{\\"invocation\\":"<<d.invocation<<",\\"frame_id\\":"<<d.frame<<",\\"request_ns\\":"<<d.request<<",\\"dispatch_ns\\":"<<d.dispatch<<",\\"render_begin_ns\\":"<<d.begin<<",\\"draw_end_ns\\":"<<d.drawn<<",\\"convert_end_ns\\":"<<d.converted<<",\\"receive_end_ns\\":"<<d.received<<",\\"published_ns\\":"<<d.published<<"}\\n";
    }
    const auto displayStats=poses.stats();auto qlog=trace(out/"display-queue.json");
    qlog<<"{\\"published\\":"<<displayStats.published<<",\\"adopted\\":"<<displayStats.adopted<<",\\"overwritten\\":"<<displayStats.overwritten<<",\\"coalesced\\":"<<displayStats.coalesced<<",\\"high_water\\":"<<displayStats.highWater<<",\\"IPC_inflight_limit\\":1}\\n";
    displayProcess.reset();
    // All large diagnostic writes''')
entry=entry.replace('''        // Warmup image is created before the measurement epoch.
        for''','''        proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
        for''')
entry=entry.replace('mode=="measure-5hz"||(stats.consumed', 'mode=="measure-5hz"||(stats.consumed')
entry=entry.replace('    check(auCount==encoded.submitted', '    check(displayStats.published==measured.size()&&displayStats.adopted==measured.size()&&displayStats.overwritten==0&&displayStats.coalesced==0,"Display result coverage differs");\n    check(auCount==encoded.submitted')
(src/'src/display_process_check.cpp').write_bytes(entry.encode())
timing=(src/'src/system_timing.cpp').read_text(encoding='utf-8')
timing=timing.replace('need(cases.size()==27,"Timing fixture coverage differs");','need(cases.size()==27||cases.size()==4,"Timing fixture coverage differs");\n    if(cases.size()==4){need(id>=transportBase&&id-transportBase<4,"Three-window transport id differs");return cases[id-transportBase];}')
(src/'src/process_system_timing.cpp').write_bytes(timing.encode())
# A separate input adapter accepts either4 or33 complete records; same Receiver.
header=(src/'include/timed_window_input.hpp').read_text(encoding='utf-8').replace('bool requireAll);','bool requireAll,size_t expected=33);')
(src/'include/process_window_input.hpp').write_bytes(header.encode())
entry=(src/'src/display_process_check.cpp').read_text(encoding='utf-8').replace('"timed_window_input.hpp"','"process_window_input.hpp"')
(src/'src/display_process_check.cpp').write_bytes(entry.encode())
inputSource=(src/'src/timed_window_input.cpp').read_text(encoding='utf-8').replace('"timed_window_input.hpp"','"process_window_input.hpp"').replace('bool all){','bool all,size_t expected){').replace('s.received!=33','s.received!=expected').replace('consumed_!=33','consumed_!=expected')
(src/'src/process_window_input.cpp').write_bytes(inputSource.encode())
cm=(root/'tools/pose-v1/system-timing-CMakeLists.txt').read_text(encoding='utf-8')
cm=cm.replace('system_timing_check.cpp system_timing.cpp timed_window_input.cpp','display_process_check.cpp process_system_timing.cpp process_window_input.cpp display_process.cpp display_protocol.cpp')
cm+='''
add_executable(pose_display_worker display_worker.cpp display_protocol.cpp skeleton_render.cpp)
target_include_directories(pose_display_worker PRIVATE .)
target_compile_options(pose_display_worker PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_display_process_selftest display_process_selftest.cpp display_process.cpp display_protocol.cpp skeleton_render.cpp)
target_include_directories(pose_display_process_selftest PRIVATE .)
target_link_libraries(pose_display_process_selftest PRIVATE Threads::Threads)
target_compile_options(pose_display_process_selftest PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
'''
(root/'tools/pose-v1/display-process-CMakeLists.txt').write_bytes(cm.encode())
builder=(root/'tools/pose-v1/Build-SystemTiming.ps1').read_text(encoding='utf-8').replace('mixed-20261008-system-timing-r1','mixed-20261008-display-process-r1')
builder=builder.replace("'pose_system_timing_selftest','--parallel'","'pose_system_timing_selftest','pose_display_worker','pose_display_process_selftest','--parallel'")
needle='$poseHashes = [ordered]@{}';builder=builder.replace(needle,"""Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_display_worker'),(Join-Path $poseOutput 'pose_display_worker'))
Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_display_process_selftest'),(Join-Path $poseOutput 'pose_display_process_selftest'))
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_display_worker'))
"""+needle)
builder=builder.replace("stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    display_worker_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_display_worker') -Algorithm SHA256).Hash.ToLowerInvariant();\n    display_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_display_process_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
(root/'tools/pose-v1/Build-DisplayProcess.ps1').write_bytes(builder.encode())
print('Created separate process target; no build or devices executed.')
