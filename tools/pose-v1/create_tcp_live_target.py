"""Create the isolated TCP diagnostic orchestration without editing frozen r2."""
from pathlib import Path
import mixed_validation_gate as old
root=old.ROOT
source=(root/'software/pose_v1/src/live_pipeline_check.cpp').read_text(encoding='utf-8')
def replace(before,after):
    global source
    assert source.count(before)==1,before
    source=source.replace(before,after)
replace('#include "online_rtsp.hpp"','#include "online_rtsp.hpp"\n#include "tcp_window_input.hpp"\n#include <cstring>')
replace('        const auto begin=Clock::now();','        pose::input::TcpWindowInput input(out/"tcp-input");')
replace('            std::this_thread::sleep_until(begin+std::chrono::milliseconds(i*500));frames.check();check(!abort,"Global stop before inference");\n            auto result=engine->process_window(cases[i].window);proof::saveVerifiedResult(cases[i],result,i,out,calls);',
'''            frames.check();check(!abort,"Global stop before inference");
            auto actual=input.next();
            check(actual.frame_id==cases[i].window.frame_id&&actual.source_time_ns==cases[i].window.source_time_ns,
                  "Received CSI identity differs from diagnostic oracle");
            check(std::memcmp(actual.csi.data(),cases[i].window.csi.data(),sizeof(actual.csi))==0,
                  "Received CSI payload differs from diagnostic oracle");
            auto result=engine->process_window(actual);proof::saveVerifiedResult(cases[i],result,i,out,calls);''')
replace('        engine->save_evidence(); // Engine stays alive while encoding repeats/drains.',
        '        input.finish(cases.size());\n        engine->save_evidence(); // Engine stays alive while encoding repeats/drains.')
dest=root/'software/pose_v1/src/live_tcp_pipeline_check.cpp'
assert not dest.exists();dest.write_bytes(source.encode())
cmake=(root/'tools/pose-v1/guarded-live-CMakeLists.txt').read_text(encoding='utf-8')
cmake=cmake.replace('live_pipeline_check.cpp pipeline_fixture_source.cpp','live_tcp_pipeline_check.cpp tcp_window_input.cpp tcp_receiver.cpp pipeline_fixture_source.cpp')
cmake+='''\nadd_executable(pose_tcp_transport_check tcp_transport_check.cpp tcp_receiver.cpp)
target_include_directories(pose_tcp_transport_check PRIVATE .)
target_link_libraries(pose_tcp_transport_check PRIVATE Threads::Threads)
target_compile_options(pose_tcp_transport_check PRIVATE -Wall -Wextra -Wpedantic)
'''
(root/'tools/pose-v1/tcp-live-CMakeLists.txt').write_bytes(cmake.encode())
builder=(root/'tools/pose-v1/Build-GuardedLive.ps1').read_text(encoding='utf-8')
builder=builder.replace('mixed-20261008-guarded-live-r1','mixed-20261008-tcp-live-r1')
builder=builder.replace("'pose_live_pipeline_check','pose_access_unit_selftest','--parallel'", "'pose_live_pipeline_check','pose_access_unit_selftest','pose_tcp_transport_check','--parallel'")
builder=builder.replace('$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_tcp_transport_check'),(Join-Path $poseOutput 'pose_tcp_transport_check'))\n$poseHashes = [ordered]@{}")
builder=builder.replace("stage='compiled_not_executed'; container='FPAI';", "stage='compiled_not_executed'; container='FPAI';\n    tcp_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_tcp_transport_check') -Algorithm SHA256).Hash.ToLowerInvariant();")
(root/'tools/pose-v1/Build-TcpLive.ps1').write_bytes(builder.encode())
