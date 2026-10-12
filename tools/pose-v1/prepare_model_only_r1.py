"""Add one no-video entry while retaining every previous model/bridge source."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def text(p):return (root/p).read_text(encoding='utf-8')
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=root/'.local/pose-v1-plddr-position/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
cm=text('tools/pose-v1/plddr-position-CMakeLists.txt')+'''
add_executable(pose_model_only_check model_only_check.cpp model_only_run.cpp pipeline_fixture_source.cpp presaved_result_evidence.cpp application_core.cpp application_bridge.cpp host_cpu_adapter.cpp preprocess.cpp host_failure_evidence.cpp failure_source_readback.cpp host_stage_observation.cpp invocation_evidence.cpp producer_count_observation.cpp tensor_identity_observation.cpp)
target_include_directories(pose_model_only_check PRIVATE .)
target_link_libraries(pose_model_only_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_model_only_check PRIVATE -Wall -Wextra -Wpedantic -ffp-contract=off)
add_executable(pose_model_only_selftest model_only_selftest.cpp model_only_run.cpp invocation_evidence.cpp)
target_include_directories(pose_model_only_selftest PRIVATE .)
target_link_libraries(pose_model_only_selftest PRIVATE Threads::Threads)
target_compile_options(pose_model_only_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
put('tools/pose-v1/model-only-CMakeLists.txt',cm)
builder=text('tools/pose-v1/Build-PlddrPosition.ps1').replace('mixed-20261010-plddr-position-r1','mixed-20261010-model-only-r1')
builder=change(builder,"'pose_plddr_position_selftest','--parallel'","'pose_plddr_position_selftest','pose_model_only_check','pose_model_only_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_model_only_check'),(Join-Path $poseOutput 'pose_model_only_check'))\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_model_only_selftest'),(Join-Path $poseOutput 'pose_model_only_selftest'))\nInvoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_model_only_check'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    model_only_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_model_only_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    model_only_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_model_only_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-ModelOnly.ps1',builder)
review=text('tools/pose-v1/review_position_build.py').replace('Build-PlddrPosition.ps1','Build-ModelOnly.ps1')
review=change(review,"'position_frozen_sources')","'position_frozen_sources','model_only_frozen_sources')")
# Original child listing precedes new model listing; inspect it by explicit file name.
review=change(review,"child_dynamic=log.rsplit('Dynamic section',1)[-1]","sections=log.split('Dynamic section');assert len(sections)==4;child_dynamic=sections[2]")
put('tools/pose-v1/review_model_only_build_base.py',review)
m['model_only_frozen_sources']={rel:item['sha256'] for rel,item in m['build_files'].items()}
old='tools/pose-v1/plddr-position-CMakeLists.txt';new='tools/pose-v1/model-only-CMakeLists.txt';m['build_files'].pop(old);m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(root/new))
for p in ['include/model_only_run.hpp','src/model_only_run.cpp','src/model_only_selftest.cpp','src/model_only_check.cpp']:
    rel='software/pose_v1/'+p;m['build_files'][rel]=dict(destination=Path(p).name,sha256=g.sha(root/rel))
for n in ['prepare_model_only_r1.py','Build-ModelOnly.ps1','review_model_only_build_base.py','run-model-only.sh']:
    rel='tools/pose-v1/'+n;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ModelOnly.ps1';m['model_only']=dict(stages=['contracts','three','load-103'],windows=[4,103],period_ns=[500000000,200000000],total_seconds=180,engine_init_seconds=60,video=False,network=False,normal_source_reads_added=0,save_before_compare=True)
out=root/'.local/pose-v1-model-only/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
