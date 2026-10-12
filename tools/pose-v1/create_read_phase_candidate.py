"""Prepare isolated read-return/pre-CPU evidence; frozen parents are never edited."""
import json, shutil
import mixed_validation_gate as g
r=g.ROOT
def read(p):return (r/p).read_text(encoding='utf-8')
def fresh(p,s):
    target=r/p
    if target.exists():assert target.read_text(encoding='utf-8')==s;return
    target.write_text(s,encoding='utf-8',newline='\n')
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)

bridge=read('software/pose_v1/src/read_input_bridge.cpp')
bridge=once(bridge,'#include "input_read_sdk.hpp"','#include "input_read_sdk.hpp"\n#include "read_phase_sdk.hpp"')
original='if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}'
bridge=once(bridge,original,'if(op->op_id==192&&index==1){pose::read_phase_sdk::copy(frame_id,invocation_id,src,dst,host(src));}else{'+original+'}')
bridge=once(bridge,'try{observation.validate();computed=cpu::forward(op,staged,{});}',
            'try{observation.validate();if(op->op_id==192){pose::read_phase_sdk::beforeCPU(staged.at(1));}computed=cpu::forward(op,staged,{});}')
bridge=once(bridge,'// Successful path unchanged. All snapshots own bytes from existing Host staging.',
            'if(op->op_id==192){pose::read_phase_sdk::error(error.what());}\n        // Original failure path and late source reads are preserved.')
fresh('software/pose_v1/src/read_phase_bridge.cpp',bridge)
main=read('software/pose_v1/src/upstream_boundary_check_r4.cpp')
main=once(main,'#include "upstream_boundary_sdk.hpp"','#include "upstream_boundary_sdk.hpp"\n#include "read_phase_sdk.hpp"')
main=once(main,'pose::upstream_sdk::configure(out/"upstream-boundary");','pose::upstream_sdk::configure(out/"upstream-boundary");\n        pose::read_phase_sdk::configure(out/"read-phase");')
marker='pose::invocation_evidence::flush({{"upstream-boundary",[]{pose::upstream_sdk::save();}}},failure,out/"upstream-persistence-ledger.json");'
main=once(main,marker,marker+'\n    pose::invocation_evidence::flush({{"read-phase",[]{pose::read_phase_sdk::save();}}},failure,out/"read-phase-persistence-ledger.json");')
fresh('software/pose_v1/src/read_phase_check.cpp',main)
cm=read('tools/pose-v1/upstream-boundary-CMakeLists.txt');start=cm.index('add_executable(pose_upstream_boundary_check ');end=cm.index('add_executable(pose_upstream_boundary_selftest ',start)
block=cm[start:end].replace('pose_upstream_boundary_check','pose_read_phase_check').replace('upstream_boundary_check.cpp','read_phase_check.cpp').replace('read_input_bridge.cpp','read_phase_bridge.cpp').replace('upstream_boundary_sdk.cpp','upstream_boundary_sdk.cpp read_phase_sdk.cpp read_phase.cpp')
extra='''
add_executable(pose_read_phase_selftest read_phase_selftest.cpp read_phase.cpp)
target_include_directories(pose_read_phase_selftest PRIVATE .)
target_link_libraries(pose_read_phase_selftest PRIVATE Threads::Threads)
target_compile_options(pose_read_phase_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
add_executable(pose_read_phase_sdk_selftest read_phase_sdk_selftest.cpp read_phase_sdk.cpp read_phase.cpp input_read_sdk.cpp input_read_contract.cpp)
target_include_directories(pose_read_phase_sdk_selftest PRIVATE .)
target_link_libraries(pose_read_phase_sdk_selftest PRIVATE Icraft::HostBackend Threads::Threads)
target_compile_options(pose_read_phase_sdk_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
fresh('tools/pose-v1/read-phase-CMakeLists.txt',cm+block+extra)
ps=read('tools/pose-v1/Build-UpstreamBoundary.ps1')
ps=once(ps,"'mixed-20261011-upstream-boundary-r1'","'mixed-20261011-read-phase-r1'")
ps=once(ps,"'--target','pose_upstream_boundary_check','pose_upstream_boundary_selftest','pose_upstream_boundary_sdk_selftest'","'--target','pose_read_phase_check','pose_read_phase_selftest','pose_read_phase_sdk_selftest'")
ps=once(ps,"':'+$poseRemote+'/build/'+$poseUpstream","':/tmp/pose-v1-mixed-20261011-upstream-boundary-r4/build/'+$poseUpstream")
ps=once(ps,"($poseRemote+'/build/pose_upstream_boundary_check')","('/tmp/pose-v1-mixed-20261011-upstream-boundary-r4/build/pose_upstream_boundary_check')")
ps=once(ps,"'.local/pose-v1-build/mixed-20261010-final-evidence-r2'","'.local/pose-v1-build/mixed-20261011-upstream-boundary-r4'")
extra_ps='''foreach ($posePhase in @('pose_read_phase_check','pose_read_phase_selftest','pose_read_phase_sdk_selftest')) {
    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$posePhase),(Join-Path $poseOutput $posePhase))
}
Invoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_read_phase_check'))
'''
ps=once(ps,'$poseHashes = [ordered]@{}',extra_ps+'$poseHashes = [ordered]@{}')
ps=once(ps,"    stage='compiled_not_executed';","    phase_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_read_phase_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    phase_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_read_phase_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    phase_sdk_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_read_phase_sdk_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    stage='compiled_not_executed';")
fresh('tools/pose-v1/Build-ReadPhase.ps1',ps)
base=read('tools/pose-v1/review_upstream_boundary_r4_build_base.py').replace('Build-UpstreamBoundary.ps1','Build-ReadPhase.ps1').replace("'upstream_r3_frozen_sources')","'upstream_r3_frozen_sources','read_phase_frozen_sources')").replace('len(sections)==11','len(sections)==12').replace('Built target pose_upstream_boundary_check','Built target pose_read_phase_check').replace("'.local/pose-v1-build/mixed-20261010-final-evidence-r2'","'.local/pose-v1-build/mixed-20261011-upstream-boundary-r4'").replace('len(proof)==36','len(proof)==39')
fresh('tools/pose-v1/review_read_phase_build_base.py',base)
stage=read('tools/pose-v1/review_upstream_boundary_r4_stage.py').replace('review_upstream_boundary_r4_build_base','review_read_phase_build_base').replace('upstream_binary_sha256','phase_binary_sha256').replace('pose_upstream_boundary_check','pose_read_phase_check').replace('run-upstream-boundary.sh','run-read-phase.sh')
fresh('tools/pose-v1/review_read_phase_stage.py',stage)
runner=read('tools/pose-v1/run-upstream-boundary.sh').replace('upstream_binary_sha256','phase_binary_sha256').replace('pose_upstream_boundary_check','pose_read_phase_check')
marker='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
tests='''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_read_phase_selftest" "$run/pose_read_phase_selftest"
    timeout --signal=TERM --kill-after=2s 20s "$work/pose_read_phase_selftest" "$run/read-phase-contracts" > "$run/read-phase-contracts.stdout.log" 2> "$run/read-phase-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/read-phase-contracts.exit.txt"
fi
if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_read_phase_sdk_selftest" "$run/pose_read_phase_sdk_selftest"
    timeout --signal=TERM --kill-after=2s 30s "$work/pose_read_phase_sdk_selftest" "$package/graph/piw24_ZG.json" "$run/read-phase-sdk-contracts" > "$run/read-phase-sdk-contracts.stdout.log" 2> "$run/read-phase-sdk-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/read-phase-sdk-contracts.exit.txt"
fi
'''
runner=once(runner,marker,tests+marker);fresh('tools/pose-v1/run-read-phase.sh',runner)
prior=r/'.local/pose-v1-upstream-boundary/package-20261011-r4';g.verify(prior);m=g.load(prior/'manifest.json');m['read_phase_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
m['build_files'].pop('tools/pose-v1/upstream-boundary-CMakeLists.txt')
for name in ['read_phase.hpp','read_phase_sdk.hpp']:
    rel='software/pose_v1/include/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(r/rel))
for name in ['read_phase.cpp','read_phase_sdk.cpp','read_phase_selftest.cpp','read_phase_sdk_selftest.cpp','read_phase_bridge.cpp','read_phase_check.cpp']:
    rel='software/pose_v1/src/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(r/rel))
rel='tools/pose-v1/read-phase-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=g.sha(r/rel))
for name in ['create_read_phase_candidate.py','Build-ReadPhase.ps1','review_read_phase_build_base.py','review_read_phase_stage.py','run-read-phase.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(r/rel)
m['build_script']='tools/pose-v1/Build-ReadPhase.ps1'
m['read_phase']=dict(op=192,slot=1,bytes=16800,snapshots=2,first4_last=True,maximum_rows=103,no_second_read=True,no_repair=True,frozen_ELFs=39,read_completion_not_DMA_proof=True)
out=r/'.local/pose-v1-read-phase/package-20261011-r1';assert not out.exists();shutil.copytree(prior,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print('Read-phase package prepared, no device/tests executed:',g.verify(out),len(m['build_files']))
