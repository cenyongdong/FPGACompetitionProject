"""Isolated bounded103 orchestration, frozen error/Engine/math and selective references."""
from pathlib import Path
import json, shutil
import mixed_validation_gate as old
root=old.ROOT
def put(rel,text):
    p=root/rel
    if p.exists():assert p.read_text(encoding='utf-8')==text,p
    else:p.write_text(text,encoding='utf-8',newline='\n')
def replace(text,before,after,count=1):
    assert text.count(before)==count,(before,text.count(before));return text.replace(before,after)

entry=(root/'software/pose_v1/src/source_readback_check_r4.cpp').read_text(encoding='utf-8')
entry=replace(entry,'#include "system_timing.hpp"','#include "system_timing.hpp"\n#include "bounded_load_contract.hpp"\n#include "bounded_frame_reference.hpp"')
entry=replace(entry,'const std::string mode=argv[1];','namespace load=pose::bounded_load;\n    const std::string mode=argv[1];')
entry=replace(entry,'host-check|process-three|measure-2hz|measure-5hz|trace-5hz','host-check|process-three|load-103')
entry=replace(entry,'host||mode=="process-three"||mode=="measure-2hz"||(mode=="measure-5hz"||mode=="trace-5hz")','host||mode=="process-three"||mode=="load-103"')
entry=replace(entry,'reserve(33)','reserve(load::sentLimit)',2)
entry=replace(entry,'net::serveOwnedAccessUnits(channel,{},out/"network");','net::RtspOptions options;options.maximumSeconds=mode=="load-103"?load::networkSeconds:90;net::serveOwnedAccessUnits(channel,options,out/"network");')
entry=replace(entry,'sampled-initialized>=20000000000ULL','sampled-initialized>=(mode=="load-103"?load::readyDurationNs:20000000000ULL)')
entry=replace(entry,'cfg.timing_frames=mode=="trace-5hz"?32:0;','cfg.timing_frames=0;')
entry=replace(entry,'input.finish(out,!(mode=="measure-5hz"||mode=="trace-5hz"),mode=="process-three"?4:33);','input.finish(out,mode=="process-three",mode=="process-three"?4:load::sentLimit);')
entry=replace(entry,'(mode=="measure-5hz"||mode=="trace-5hz")','mode=="load-103"')
line='for(size_t i=0;i<measured.size();++i){const auto& r=measured[i].result;auto rgb=rr::draw(r.scores,r.poses,r.frame_id);auto pixels=rr::yuv420sp(rgb.rgb,rr::width,rr::height,false);proof::persistBytes(out/"frames"/("result"+std::to_string(i)+".nv12"),pixels.data(),pixels.size());}'
entry=replace(entry,line,'load::saveFrameReferences(measured,cases,out);')
put('software/pose_v1/src/bounded_load_check_r1.cpp',entry)
header=(root/'software/pose_v1/include/system_timing.hpp').read_text(encoding='utf-8')
header=replace(header,'#include "tcp_receiver.hpp"','#include "tcp_receiver.hpp"\n#include "bounded_load_contract.hpp"')
header=replace(header,'sentLimit=33, warmups=3','sentLimit=pose::bounded_load::sentLimit, warmups=pose::bounded_load::warmups')
put('software/pose_v1/include/bounded_system_timing.hpp',header)
worker=(root/'software/pose_v1/src/display_worker.cpp').read_text(encoding='utf-8')
worker=replace(worker,'#include "skeleton_render.hpp"','#include "skeleton_render.hpp"\n#include "bounded_load_contract.hpp"')
worker=replace(worker,'renders<33','renders<pose::bounded_load::sentLimit')
put('software/pose_v1/src/bounded_display_worker.cpp',worker)
selftest=(root/'software/pose_v1/src/system_timing_selftest.cpp').read_text(encoding='utf-8');selftest=replace(selftest,'fixtureFor(cases,100033)','fixtureFor(cases,100103)')
put('software/pose_v1/src/bounded_system_timing_selftest.cpp',selftest)
cm=(root/'tools/pose-v1/source-readback-r4-CMakeLists.txt').read_text(encoding='utf-8');cm=replace(cm,'forward_trace_check.cpp process_system_timing.cpp','forward_trace_check.cpp bounded_frame_reference.cpp process_system_timing.cpp')
cm+='\nadd_executable(pose_bounded_load_selftest bounded_load_selftest.cpp display_process.cpp display_protocol.cpp skeleton_render.cpp)\ntarget_include_directories(pose_bounded_load_selftest PRIVATE .)\ntarget_link_libraries(pose_bounded_load_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_bounded_load_selftest PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)\n'
put('tools/pose-v1/bounded-load-CMakeLists.txt',cm)
builder=(root/'tools/pose-v1/Build-SourceReadbackR4.ps1').read_text(encoding='utf-8').replace('mixed-20261009-source-readback-r4','mixed-20261009-bounded-load-r1')
builder=replace(builder,"'pose_failure_evidence_selftest','--parallel'","'pose_failure_evidence_selftest','pose_bounded_load_selftest','--parallel'")
builder=replace(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_bounded_load_selftest'),(Join-Path $poseOutput 'pose_bounded_load_selftest'))\nInvoke-MixedDocker @('exec',$poseContainer,'g++','-std=c++17','-O2','-ffp-contract=off',('-I'+$poseRemote+'/source'),$poseRemote+'/source/bounded_reference_export.cpp',$poseRemote+'/source/skeleton_render.cpp','-o',$poseRemote+'/build/pose_bounded_reference_export.native')\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_bounded_reference_export.native'),(Join-Path $poseOutput 'pose_bounded_reference_export.native'))\n$poseHashes = [ordered]@{}")
builder=replace(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    bounded_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_bounded_load_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    native_reference_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_bounded_reference_export.native') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-BoundedLoad.ps1',builder)
runner=(root/'tools/pose-v1/run-source-readback-r4.sh').read_text(encoding='utf-8')
runner=replace(runner,'host-check / process-three / measure-2hz / measure-5hz / trace-5hz','host-check / process-three / load-103')
runner=replace(runner,'measure-2hz) previous=process-three; seconds=180;; measure-5hz) previous=measure-2hz; seconds=180;; trace-5hz) previous=process-three; seconds=180;;','load-103) previous=process-three; seconds=180;;')
needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
runner=replace(runner,needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_bounded_load_selftest" "$run/pose_bounded_load_selftest"
    timeout --signal=TERM --kill-after=2s 60s "$work/pose_bounded_load_selftest" "$work/pose_display_worker" "$run/bounded-contracts" > "$run/bounded-contracts.stdout.log" 2> "$run/bounded-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/bounded-contracts.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-bounded-load.sh',runner)
review=(root/'tools/pose-v1/review_source_r4_stage.py').read_text(encoding='utf-8').replace('Build-SourceReadbackR4.ps1','Build-BoundedLoad.ps1').replace('run-source-readback-r4.sh','run-bounded-load.sh')
review=replace(review,"'source_r4_frozen_sources')","'source_r4_frozen_sources','bounded_frozen_sources')")
review=replace(review,"'measure-2hz','measure-5hz','trace-5hz'","'load-103'")
review=replace(review,"'measure-2hz':'process-three','measure-5hz':'measure-2hz','trace-5hz':'process-three'","'load-103':'process-three'")
review=replace(review,"<=33","<=103")
review=replace(review,"expected=4 if a.stage=='process-three' else 33","expected=4 if a.stage=='process-three' else 103")
review=replace(review,"'measure-2hz','process-three'","'process-three',")
review=replace(review,"a.stage!='trace-5hz'","a.stage=='load-103'")
needle="assert not (r/'stderr.log').read_bytes();report.update(Host_cases=107"
review=replace(review,needle,"assert load(r/'bounded-contracts.stdout.log')==dict(status='passed',mapping=103,renders=206,refusals=5,sparse_references=29,SDK_device=False)\n            assert (r/'bounded-contracts.exit.txt').read_text(encoding='utf-8').strip()=='0' and not (r/'bounded-contracts.stderr.log').read_bytes()\n            "+needle)
needle="assert not load(out/'engine/sdk-profile-setting.json')['enabled'];catalog="
review=replace(review,needle,"assert all((out/'engine'/f).stat().st_size==0 for f in ['monotonic-spans.jsonl','readiness.jsonl','operator-execution.jsonl'])\n            assert not (out/'failed-host-inputs').exists()\n            "+needle)
put('tools/pose-v1/review_bounded_load_stage.py',review)
client=(root/'tools/pose-v1/live_rtsp_client.py').read_text(encoding='utf-8');client=replace(client,'time.perf_counter()-start<95','time.perf_counter()-start<105')
put('tools/pose-v1/bounded_live_rtsp_client.py',client)
peer=(root/'tools/pose-v1/source_coverage_peer_ready.py').read_text(encoding='utf-8')
start=peer.index('from source_readback_peer_stream_ready import StreamReadyClient');end=start+len('from source_readback_peer_stream_ready import StreamReadyClient')
ready=(root/'tools/pose-v1/source_readback_peer_stream_ready.py').read_text(encoding='utf-8');ready=ready[ready.index('class StreamReadyClient'):ready.index('\ndef main():')]
peer=peer[:start]+'from bounded_live_rtsp_client import LiveClient\n\n'+ready+peer[end:]
peer=peer.replace('33','103').replace("'source_readback_peer_stream_ready.py'","'bounded_live_rtsp_client.py'")
put('tools/pose-v1/bounded_load_peer_ready.py',peer)
base=root/'.local/pose-v1-source-readback/package-20261009-r4';old.verify(base);m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
mapping={
'software/pose_v1/src/source_readback_check_r4.cpp':'software/pose_v1/src/bounded_load_check_r1.cpp',
'software/pose_v1/include/system_timing.hpp':'software/pose_v1/include/bounded_system_timing.hpp',
'software/pose_v1/src/display_worker.cpp':'software/pose_v1/src/bounded_display_worker.cpp',
'software/pose_v1/src/system_timing_selftest.cpp':'software/pose_v1/src/bounded_system_timing_selftest.cpp',
'tools/pose-v1/source-readback-r4-CMakeLists.txt':'tools/pose-v1/bounded-load-CMakeLists.txt'}
m['bounded_frozen_sources']={rel:old.sha(root/rel) for rel in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=old.sha(root/after))
for rel in ['include/bounded_load_contract.hpp','include/bounded_frame_reference.hpp','src/bounded_frame_reference.cpp','src/bounded_load_selftest.cpp','src/bounded_reference_export.cpp']:
    source='software/pose_v1/'+rel;m['build_files'][source]=dict(destination=Path(rel).name,sha256=old.sha(root/source))
for name in ['prepare_bounded_load_r1.py','Build-BoundedLoad.ps1','run-bounded-load.sh','review_bounded_load_stage.py','bounded_live_rtsp_client.py','bounded_load_peer_ready.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
m['build_script']='tools/pose-v1/Build-BoundedLoad.ps1';m['bounded_load']=dict(frames=103,warmups=3,ready_seconds=30,network_seconds=100,client_seconds=105,outer_seconds=180,normal_error_reads_retained=True,operator_trace=False,ARM_postrun_sparse_references=True)
out=root/'.local/pose-v1-bounded-load/package-20261009-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(old.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(json.dumps(dict(payloads=old.verify(out),build_sources=len(m['build_files']))))
