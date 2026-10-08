"""Create isolated timing target; frozen functional/diagnostic implementations stay intact."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];src=root/'software/pose_v1'
entry=(src/'src/live_tcp_presaved_check.cpp').read_text(encoding='utf-8')
entry=entry.replace('#include "tcp_window_input.hpp"','#include "timed_window_input.hpp"\n#include "system_timing.hpp"\n#include <sstream>')
entry=entry.replace('host-check|live-three|live-27','host-check|measure-2hz|measure-5hz').replace('mode=="live-three"||mode=="live-27"','mode=="measure-2hz"||mode=="measure-5hz"')
entry=entry.replace('auto cases=proof::fixtureWindows(package,mode=="live-27");','auto cases=proof::fixtureWindows(package,true);cases.pop_back();std::vector<pose::measurement::Measurement> measured;measured.reserve(33);')
entry=entry.replace('auto calls=trace(out/"inference.jsonl"),samples=trace(out/"samples.jsonl"),packets=trace(out/"packets.jsonl"),lifecycle=trace(out/"lifecycle.jsonl"),auLog=trace(out/"access-units.jsonl");','std::ostringstream samples,packets,auLog;auto lifecycle=trace(out/"lifecycle.jsonl");')
entry=entry.replace('samples<<','samples<<').replace('<<std::endl;\n                return vv::ResidentSample','<<\'\\n\';\n                return vv::ResidentSample')
entry=entry.replace('if(auto frame=frames.popLatest())latest=std::move(frame);','const auto adopt=ns();if(auto frame=frames.popLatest())latest=std::move(frame);')
entry=entry.replace('<<",\\\"generated_ns\\\":"<<frame.generatedNs','<<",\\\"adopt_ns\\\":"<<adopt<<",\\\"generated_ns\\\":"<<frame.generatedNs')
entry=entry.replace('<<",\\\"bytes\\\":"<<packet.bytes.size()', '<<",\\\"capture_ns\\\":"<<ns()<<",\\\"bytes\\\":"<<packet.bytes.size()')
entry=entry.replace('<<packet.flags<<"}"<<std::endl;', '<<packet.flags<<"}"<<\'\\n\';')
entry=entry.replace('<<unit->slice.size()<<"}"<<std::endl;', '<<unit->slice.size()<<"}"<<\'\\n\';')
entry=entry.replace('cfg.diagnostic_frames=4','cfg.diagnostic_frames=0')
start=entry.index('        pose::input::TcpWindowInput input(')
end=entry.index('\n    }catch(...){fail',start)
entry=entry[:start]+'''        pose::measurement::TimedWindowInput input;
        while(auto item=input.next()){
            frames.check();check(!abort,"Global stop before timing inference");
            check(measured.size()<pose::measurement::sentLimit,"Timing owned results capacity exceeded");
            check(item->sequence==item->window.frame_id-pose::measurement::transportBase,"Transport sequence differs");
            pose::measurement::Measurement record;record.item=std::move(*item);record.dequeued=ns();
            const auto& fixture=pose::measurement::fixtureFor(cases,record.item.window.frame_id);
            check(record.item.window.source_time_ns==fixture.window.source_time_ns&&std::memcmp(record.item.window.csi.data(),fixture.window.csi.data(),sizeof(record.item.window.csi))==0,"Timing raw payload differs");
            record.processBegin=ns();record.result=engine->process_window(record.item.window);record.processEnd=ns();
            // Preserve the complete returned value even if the unchanged gate fails.
            measured.push_back(std::move(record));auto& v=measured.back();
            pose::measurement::verify(fixture,v.result,v.item.window,measured.size()-1);v.verifyEnd=ns();
            auto rgb=rr::draw(v.result.scores,v.result.poses,v.result.frame_id);v.drawEnd=ns();
            for(const auto& point:rgb.projected)check(point[1]<590,"Joint overlaps diagnostic marker");
            vv::OwnedFrame frame;frame.nv12=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);v.convertEnd=ns();
            frame.sourceFrame=v.result.frame_id;frame.invocation=v.result.invocation;frame.generatedNs=v.convertEnd;
            frames.publish(std::move(frame));v.published=ns();
        }
        input.finish(out,mode=="measure-2hz");
''' + entry[end:]
entry=entry.replace('    engine.reset();lifecycle', '''    // All large diagnostic writes happen after workers complete, outside the measurement.
    try{
        pose::measurement::save(measured,cases,out);if(engine)engine->save_evidence();
        proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
        for(size_t i=0;i<measured.size();++i){const auto& r=measured[i].result;auto rgb=rr::draw(r.scores,r.poses,r.frame_id);auto pixels=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);proof::persistBytes(out/"frames"/("result"+std::to_string(i)+".nv12"),pixels.data(),pixels.size());}
    }catch(...){if(!failure)failure=std::current_exception();}
    for(auto pair:{std::make_pair("samples.jsonl",samples.str()),std::make_pair("packets.jsonl",packets.str()),std::make_pair("access-units.jsonl",auLog.str())}){auto f=trace(out/pair.first);f<<pair.second;}
    engine.reset();lifecycle''')
entry=entry.replace('stats.published==cases.size()&&stats.consumed==cases.size()&&stats.overwritten==0&&stats.coalesced==0','stats.published==measured.size()&&(mode=="measure-5hz"||(stats.consumed==measured.size()&&stats.overwritten==0&&stats.coalesced==0))')
entry=entry.replace('<<cases.size()<<",\\\"encoded_frames','<<measured.size()<<",\\\"encoded_frames')
entry=entry.replace('proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());','// Warmup image is created before the measurement epoch.')
(src/'src/system_timing_check.cpp').write_bytes(entry.encode())
# Only log buffering/timestamps differ; IOCTL, cookies, copies and pacing stay identical.
vpu=(src/'src/vpu_resident_encoder.cpp').read_text(encoding='utf-8').replace('<<std::endl','<<\'\\n\'')
(src/'src/timed_resident_encoder.cpp').write_bytes(vpu.encode())
net=(src/'src/guarded_rtsp.cpp').read_text(encoding='utf-8')
net=net.replace('<<std::endl','<<\'\\n\'')
net=net.replace('\\\"nal_delivered\\\",\\\"source\\\":','\\\"nal_delivered\\\",\\\"handoff_ns\\\":"<<std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::steady_clock::now().time_since_epoch()).count()<<",\\\"source\\\":')
needle='s.log<<"{\\\"event\\\":\\\"ready\\\",\\\"port\\\":"<<s.options.port<<",\\\"owned_AU\\\":true}"<<\'\\n\';'
assert needle in net;net=net.replace(needle,needle+'s.log.flush();')
(src/'src/timed_guarded_rtsp.cpp').write_bytes(net.encode())
cm=(root/'tools/pose-v1/tcp-presaved-CMakeLists.txt').read_text(encoding='utf-8')
cm=cm.replace('live_tcp_presaved_check.cpp','system_timing_check.cpp system_timing.cpp timed_window_input.cpp').replace(' tcp_window_input.cpp','').replace('vpu_resident_encoder.cpp','timed_resident_encoder.cpp').replace(' guarded_rtsp.cpp',' timed_guarded_rtsp.cpp')
cm+='''
add_executable(pose_system_timing_selftest system_timing_selftest.cpp system_timing.cpp presaved_result_evidence.cpp pipeline_fixture_source.cpp preprocess.cpp)
target_include_directories(pose_system_timing_selftest PRIVATE .)
target_compile_options(pose_system_timing_selftest PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
'''
(root/'tools/pose-v1/system-timing-CMakeLists.txt').write_bytes(cm.encode())
builder=(root/'tools/pose-v1/Build-TcpPresaved.ps1').read_text(encoding='utf-8').replace('mixed-20261008-tcp-presaved-r1','mixed-20261008-system-timing-r1')
builder=builder.replace("'pose_failed_result_selftest','--parallel'","'pose_failed_result_selftest','pose_system_timing_selftest','--parallel'")
needle="$poseHashes = [ordered]@{}"
builder=builder.replace(needle,"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_system_timing_selftest'),(Join-Path $poseOutput 'pose_system_timing_selftest'))\n"+needle)
builder=builder.replace("stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    timing_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_system_timing_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
(root/'tools/pose-v1/Build-SystemTiming.ps1').write_bytes(builder.encode())
print('Created isolated timing sources, no devices or compilation executed.')
