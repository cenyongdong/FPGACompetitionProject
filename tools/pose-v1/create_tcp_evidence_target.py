"""Capture a rejected result without changing the validated gate or Engine."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
source=(root/'software/pose_v1/src/live_tcp_pipeline_check.cpp').read_text(encoding='utf-8')
source=source.replace('#include "tcp_window_input.hpp"','#include "tcp_window_input.hpp"\n#include "failed_result_evidence.hpp"')
assert source.count('proof::saveVerifiedResult(cases[i],result,i,out,calls);')==1
source=source.replace('proof::saveVerifiedResult(cases[i],result,i,out,calls);','proof::saveOrCaptureFailedResult(cases[i],result,actual,i,out,calls);')
target=root/'software/pose_v1/src/live_tcp_evidence_check.cpp';assert not target.exists();target.write_bytes(source.encode())
cmake=(root/'tools/pose-v1/tcp-live-CMakeLists.txt').read_text(encoding='utf-8').replace('live_tcp_pipeline_check.cpp tcp_window_input.cpp','live_tcp_evidence_check.cpp failed_result_evidence.cpp tcp_window_input.cpp')
cmake+='''\nadd_executable(pose_failed_result_selftest failed_result_selftest.cpp failed_result_evidence.cpp pipeline_fixture_source.cpp preprocess.cpp)
target_include_directories(pose_failed_result_selftest PRIVATE .)
target_compile_options(pose_failed_result_selftest PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
'''
(root/'tools/pose-v1/tcp-evidence-CMakeLists.txt').write_bytes(cmake.encode())
builder=(root/'tools/pose-v1/Build-TcpLive.ps1').read_text(encoding='utf-8').replace('mixed-20261008-tcp-live-r1','mixed-20261008-tcp-evidence-r1')
builder=builder.replace("'pose_tcp_transport_check','--parallel'","'pose_tcp_transport_check','pose_failed_result_selftest','--parallel'")
builder=builder.replace('$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_failed_result_selftest'),(Join-Path $poseOutput 'pose_failed_result_selftest'))\n$poseHashes = [ordered]@{}")
builder=builder.replace("stage='compiled_not_executed'; container='FPAI';", "stage='compiled_not_executed'; container='FPAI';\n    failed_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_failed_result_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
(root/'tools/pose-v1/Build-TcpEvidence.ps1').write_bytes(builder.encode())
