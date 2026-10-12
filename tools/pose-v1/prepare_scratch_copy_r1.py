"""New owned-scratch copy target; old192 probe/main source is preserved."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def put(p,text):p=root/p;assert not p.exists();p.write_text(text,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=root/'.local/pose-v1-producer-count/package-20261009-r2';g.verify(base);m=g.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert g.sha(root/rel)==item['sha256']
cm=read('tools/pose-v1/producer-count-CMakeLists.txt')+'''
add_executable(pose_scratch_copy_check scratch_copy_check_r1.cpp scratch_copy_pattern.cpp scratch_copy_sdk.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp invocation_evidence.cpp)
target_include_directories(pose_scratch_copy_check PRIVATE .)
target_link_libraries(pose_scratch_copy_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_scratch_copy_check PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
add_executable(pose_scratch_copy_selftest scratch_copy_pattern_selftest.cpp scratch_copy_pattern.cpp)
target_include_directories(pose_scratch_copy_selftest PRIVATE .)
target_compile_options(pose_scratch_copy_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
'''
put('tools/pose-v1/scratch-copy-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-ProducerCount.ps1').replace('mixed-20261009-producer-count-r2','mixed-20261010-scratch-copy-r1')
builder=change(builder,"'pose_producer_count_selftest','--parallel'","'pose_producer_count_selftest','pose_scratch_copy_check','pose_scratch_copy_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_scratch_copy_check'),(Join-Path $poseOutput 'pose_scratch_copy_check'))\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_scratch_copy_selftest'),(Join-Path $poseOutput 'pose_scratch_copy_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    scratch_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_scratch_copy_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    scratch_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_scratch_copy_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-ScratchCopy.ps1',builder)
runner=read('tools/pose-v1/run-producer-count.sh');needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
runner=change(runner,needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_scratch_copy_selftest" "$run/pose_scratch_copy_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_scratch_copy_selftest" "$run/scratch-contracts" > "$run/scratch-contracts.stdout.log" 2> "$run/scratch-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/scratch-contracts.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-scratch-host.sh',runner)
review=read('tools/pose-v1/review_producer_count_stage.py').replace('Build-ProducerCount.ps1','Build-ScratchCopy.ps1').replace('run-producer-count.sh','run-scratch-host.sh')
review=change(review,"'producer_count_frozen_sources')","'producer_count_frozen_sources','scratch_frozen_sources')")
put('tools/pose-v1/review_scratch_host.py',review)
m['scratch_frozen_sources']={'tools/pose-v1/producer-count-CMakeLists.txt':g.sha(root/'tools/pose-v1/producer-count-CMakeLists.txt')}
old=m['build_files'].pop('tools/pose-v1/producer-count-CMakeLists.txt');m['build_files']['tools/pose-v1/scratch-copy-CMakeLists.txt']=dict(destination=old['destination'],sha256=g.sha(root/'tools/pose-v1/scratch-copy-CMakeLists.txt'))
for name in ['include/scratch_copy_pattern.hpp','src/scratch_copy_pattern.cpp','src/scratch_copy_pattern_selftest.cpp','include/scratch_copy_sdk.hpp','src/scratch_copy_sdk.cpp','include/scratch_vpu_load.hpp','src/scratch_vpu_load.cpp','src/scratch_copy_check_r1.cpp']:
    rel='software/pose_v1/'+name;m['build_files'][rel]=dict(destination=Path(name).name,sha256=g.sha(root/rel))
for name in ['prepare_scratch_copy_r1.py','Build-ScratchCopy.ps1','run-scratch-host.sh','review_scratch_host.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ScratchCopy.ps1';m['scratch_copy']=dict(sizes=[30240,16800],pairs=100,full_model_Session=False,NPU_forward=False,device_allocations_owned=True,default_region='AXIZG330AIPLDDRMemRegionNode',pacing_inside_pair=False,pacing_between_pairs_ms_with_VPU=200,memory_seconds=30,VPU_copy_seconds=20,VPU_overall_seconds=180,copy_before_compare_snapshot=True,first_last_and_error_bytes_saved=True)
out=root/'.local/pose-v1-scratch-copy/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
