"""Isolated final-gate diagnostics; frozen sources and arithmetic remain exact."""
import json,shutil
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def fresh(p,s):
    p=root/p;assert not p.exists(),p;p.write_text(s,encoding='utf-8',newline='\n')
cm=read('tools/pose-v1/combined-read-CMakeLists.txt')
block=cm[cm.index('add_executable(pose_combined_read_check '):]
block=block.replace('pose_combined_read_check','pose_final_evidence_check').replace('combined_read_check.cpp','final_evidence_check.cpp').replace('read_input_bridge.cpp','final_evidence_bridge.cpp final_source_sdk.cpp final_source_recorder.cpp owned_result_save.cpp')
tests='''
add_executable(pose_final_source_selftest final_source_selftest.cpp final_source_recorder.cpp owned_result_save.cpp process_system_timing.cpp pipeline_fixture_source.cpp presaved_result_evidence.cpp preprocess.cpp)
target_include_directories(pose_final_source_selftest PRIVATE .)
target_link_libraries(pose_final_source_selftest PRIVATE Threads::Threads)
target_compile_options(pose_final_source_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
add_executable(pose_final_source_sdk_selftest final_source_sdk_selftest.cpp final_source_sdk.cpp final_source_recorder.cpp)
target_include_directories(pose_final_source_sdk_selftest PRIVATE .)
target_link_libraries(pose_final_source_sdk_selftest PRIVATE Icraft::HostBackend Threads::Threads)
target_compile_options(pose_final_source_sdk_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
fresh('tools/pose-v1/final-evidence-CMakeLists.txt',cm+block+tests)
ps=read('tools/pose-v1/Build-CombinedRead.ps1').replace('mixed-20261010-combined-read-r1','mixed-20261010-final-evidence-r1')
ps=ps.replace("'--parallel','2'","'pose_final_evidence_check','pose_final_source_selftest','pose_final_source_sdk_selftest','--parallel','2'",1)
ps=ps.replace('$poseHashes = [ordered]@{}',"foreach ($poseFinal in @('pose_final_evidence_check','pose_final_source_selftest','pose_final_source_sdk_selftest')) {\n    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$poseFinal),(Join-Path $poseOutput $poseFinal))\n}\nInvoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_final_evidence_check'))\n$poseHashes = [ordered]@{}",1)
ps=ps.replace("    stage='compiled_not_executed';","    final_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_final_evidence_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    final_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_final_source_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    final_sdk_contract_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_final_source_sdk_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();\n    stage='compiled_not_executed';",1)
fresh('tools/pose-v1/Build-FinalEvidence.ps1',ps)
base=read('tools/pose-v1/review_combined_read_build_base.py').replace('Build-CombinedRead.ps1','Build-FinalEvidence.ps1').replace("'combined_read_frozen_sources')","'combined_read_frozen_sources','final_evidence_frozen_sources')").replace('len(sections)==9','len(sections)==10')
fresh('tools/pose-v1/review_final_evidence_build_base.py',base)
stage=read('tools/pose-v1/review_combined_read_stage.py').replace('review_combined_read_build_base','review_final_evidence_build_base').replace('combined_binary_sha256','final_binary_sha256').replace('pose_combined_read_check','pose_final_evidence_check').replace('run-combined-read.sh','run-final-evidence.sh')
fresh('tools/pose-v1/review_final_evidence_stage.py',stage)
runner=read('tools/pose-v1/run-combined-read.sh').replace('pose_combined_read_check','pose_final_evidence_check').replace('combined_binary_sha256','final_binary_sha256')
marker='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
insert='''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_final_source_selftest" "$run/pose_final_source_selftest"
    timeout --signal=TERM --kill-after=2s 20s "$work/pose_final_source_selftest" "$run/final-contracts" > "$run/final-contracts.stdout.log" 2> "$run/final-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/final-contracts.exit.txt"
fi
if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_final_source_sdk_selftest" "$run/pose_final_source_sdk_selftest"
    timeout --signal=TERM --kill-after=2s 30s "$work/pose_final_source_sdk_selftest" "$package/graph/piw24_ZG.json" "$run/final-sdk-contracts" > "$run/final-sdk-contracts.stdout.log" 2> "$run/final-sdk-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/final-sdk-contracts.exit.txt"
fi
'''
assert marker in runner;runner=runner.replace(marker,insert+marker,1)
fresh('tools/pose-v1/run-final-evidence.sh',runner)
base=root/'.local/pose-v1-combined-read/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json');m['final_evidence_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
m['build_files'].pop('tools/pose-v1/combined-read-CMakeLists.txt')
new=['final_source_recorder.hpp','final_source_sdk.hpp','owned_result_save.hpp']
for name in new:
    rel='software/pose_v1/include/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(root/rel))
for name in ['final_source_recorder.cpp','final_source_sdk.cpp','owned_result_save.cpp','final_evidence_check.cpp','final_evidence_bridge.cpp','final_source_selftest.cpp','final_source_sdk_selftest.cpp']:
    rel='software/pose_v1/src/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(root/rel))
rel='tools/pose-v1/final-evidence-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=g.sha(root/rel))
for name in ['create_final_evidence_candidate.py','Build-FinalEvidence.ps1','run-final-evidence.sh','review_final_evidence_build_base.py','review_final_evidence_stage.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-FinalEvidence.ps1';m['final_evidence']=dict(source_nodes=[582,649],CPU_outputs=[437,582],source_bytes=67200,CPU_output_bytes=17600,read_rounds=2,physical_reuse_possible=True,save_before_gate=True,serialization_no_oracle=True,hardware_seconds=180,diagnostic_fps=5.05,not_performance_acceptance=True)
out=root/'.local/pose-v1-final-evidence/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
