"""Add standalone real-type/static/dynamic probes; freeze the latest model main."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
base=root/'.local/pose-v1-tensor-identity/package-20261010-r3';g.verify(base);m=g.load(base/'manifest.json')
cm=read('tools/pose-v1/tensor-identity-CMakeLists.txt')+'''
add_executable(pose_typed_scratch_check typed_scratch_check.cpp typed_scratch_pattern.cpp typed_scratch_sdk.cpp scratch_copy_pattern.cpp scratch_vpu_load.cpp timed_resident_encoder.cpp invocation_evidence.cpp)
target_include_directories(pose_typed_scratch_check PRIVATE .)
target_link_libraries(pose_typed_scratch_check PRIVATE Icraft::HostBackend Icraft::ZG330Backend Threads::Threads)
target_compile_options(pose_typed_scratch_check PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
add_executable(pose_typed_scratch_selftest typed_scratch_selftest.cpp typed_scratch_pattern.cpp scratch_copy_pattern.cpp)
target_include_directories(pose_typed_scratch_selftest PRIVATE .)
target_compile_options(pose_typed_scratch_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror -ffp-contract=off)
'''
put('tools/pose-v1/typed-scratch-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-TensorIdentityR3.ps1').replace('mixed-20261010-tensor-identity-r3','mixed-20261010-typed-scratch-r1')
builder=change(builder,"'pose_tensor_identity_selftest','--parallel'","'pose_tensor_identity_selftest','pose_typed_scratch_check','pose_typed_scratch_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_typed_scratch_check'),(Join-Path $poseOutput 'pose_typed_scratch_check'))\nInvoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_typed_scratch_selftest'),(Join-Path $poseOutput 'pose_typed_scratch_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    typed_binary_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_typed_scratch_check') -Algorithm SHA256).Hash.ToLowerInvariant();\n    typed_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_typed_scratch_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-TypedScratch.ps1',builder)
review=read('tools/pose-v1/review_tensor_identity_r3_stage.py').replace('Build-TensorIdentityR3.ps1','Build-TypedScratch.ps1')
review=change(review,"'tensor_identity_r2_frozen_sources')","'tensor_identity_r2_frozen_sources','typed_frozen_main_sources','typed_frozen_helpers')")
put('tools/pose-v1/review_typed_build.py',review)
before='tools/pose-v1/tensor-identity-CMakeLists.txt';after='tools/pose-v1/typed-scratch-CMakeLists.txt';m['typed_frozen_main_sources']={before:g.sha(root/before)};item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
helpers={'software/pose_v1/include/scratch_copy_pattern_r3.hpp':'scratch_copy_pattern.hpp','software/pose_v1/src/scratch_copy_pattern_r3.cpp':'scratch_copy_pattern.cpp','software/pose_v1/include/scratch_vpu_load.hpp':'scratch_vpu_load.hpp','software/pose_v1/src/scratch_vpu_load.cpp':'scratch_vpu_load.cpp'}
m['typed_frozen_helpers']={p:g.sha(root/p) for p in helpers}
for p,dest in helpers.items():m['build_files'][p]=dict(destination=dest,sha256=g.sha(root/p))
for p in ['include/typed_scratch_pattern.hpp','include/typed_scratch_sdk.hpp','src/typed_scratch_pattern.cpp','src/typed_scratch_selftest.cpp','src/typed_scratch_sdk.cpp','src/typed_scratch_check.cpp']:
    rel='software/pose_v1/'+p;m['build_files'][rel]=dict(destination=Path(p).name,sha256=g.sha(root/rel))
for name in ['prepare_typed_scratch_r1.py','Build-TypedScratch.ps1','review_typed_build.py','run-typed-scratch.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-TypedScratch.ps1';m['typed_scratch']=dict(source_op=192,values=[4386,4390],actual_types=True,maximum_pattern_index=100,stride=8192,stages=['contracts','static','dynamic','vpu'],pairs_per_stage=100,normal_read_pairs=1,normal_reads_between_pairs=0,full_model_Session=False,NPU_forward=False)
out=root/'.local/pose-v1-typed-scratch/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
