"""Create one isolated public-read candidate; all frozen sources remain intact."""
from pathlib import Path
import json,shutil
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def fresh(p,s):
    p=root/p;assert not p.exists(),p;p.write_text(s,encoding='utf-8',newline='\n')
bridge=read('software/pose_v1/src/tensor_identity_bridge_r2.cpp')
old='dst.copyFrom(0,src,0,value.tensorType().bytes());'
assert bridge.count(old)==1
bridge=bridge.replace('#include "mixed_bridge.hpp"','#include "mixed_bridge.hpp"\n#include "input_read_sdk.hpp"',1).replace(old,'if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}',1)
fresh('software/pose_v1/src/read_input_bridge.cpp',bridge)
fresh('software/pose_v1/src/input_read_host_check.cpp','#include <iostream>\nextern int mixed_host_check(int,char**);\nint main(int argc,char**argv){return mixed_host_check(argc,argv);}\n')
cm=read('tools/pose-v1/picture-CMakeLists.txt')
picture=cm[cm.index('add_executable(pose_picture_check '):cm.index('add_executable(pose_picture_source_selftest ')]
new=picture.replace('pose_picture_check','pose_picture_read_check').replace('application_bridge.cpp','read_input_bridge.cpp input_read_sdk.cpp input_read_contract.cpp')
host=new.replace('pose_picture_read_check','pose_input_read_host_check').replace('picture_check.cpp','input_read_host_check.cpp mixed_host_check.cpp')
cm+=new+host+'''
add_executable(pose_input_read_selftest input_read_selftest.cpp input_read_contract.cpp)
target_include_directories(pose_input_read_selftest PRIVATE .)
target_compile_options(pose_input_read_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
add_executable(pose_input_read_sdk_selftest input_read_sdk_selftest.cpp input_read_sdk.cpp input_read_contract.cpp)
target_include_directories(pose_input_read_sdk_selftest PRIVATE .)
target_link_libraries(pose_input_read_sdk_selftest PRIVATE Icraft::HostBackend)
target_compile_options(pose_input_read_sdk_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)
'''
fresh('tools/pose-v1/input-read-CMakeLists.txt',cm)
ps=read('tools/pose-v1/Build-Picture.ps1').replace("mixed-20261010-picture-r1","mixed-20261010-input-read-r1")
ps=ps.replace("'--parallel','2'","'pose_picture_read_check','pose_input_read_host_check','pose_input_read_selftest','pose_input_read_sdk_selftest','--parallel','2'",1)
needle='$poseHashes = [ordered]@{}'
ps=ps.replace(needle,"foreach ($poseRead in @('pose_picture_read_check','pose_input_read_host_check','pose_input_read_selftest','pose_input_read_sdk_selftest')) {\n    Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/'+$poseRead),(Join-Path $poseOutput $poseRead))\n}\nInvoke-MixedDocker @('exec',$poseContainer,'aarch64-linux-gnu-readelf','-d',($poseRemote+'/build/pose_picture_read_check'))\n"+needle,1)
ps=ps.replace("    stage='compiled_not_executed';",''.join("    "+key+"=(Get-FileHash -LiteralPath (Join-Path $poseOutput '"+name+"') -Algorithm SHA256).Hash.ToLowerInvariant();\n" for name,key in [('pose_picture_read_check','read_picture_binary_sha256'),('pose_input_read_host_check','read_host_binary_sha256'),('pose_input_read_selftest','read_selftest_sha256'),('pose_input_read_sdk_selftest','read_sdk_selftest_sha256')])+"    stage='compiled_not_executed';",1)
fresh('tools/pose-v1/Build-InputRead.ps1',ps)
review=read('tools/pose-v1/review_picture_build_base.py').replace('Build-Picture.ps1','Build-InputRead.ps1').replace("'picture_frozen_sources')","'picture_frozen_sources','input_read_frozen_sources')").replace('len(sections)==7','len(sections)==8')
fresh('tools/pose-v1/review_input_read_build_base.py',review)
review=read('tools/pose-v1/review_picture.py').replace('review_picture_build_base','review_input_read_build_base').replace('picture_binary_sha256','read_picture_binary_sha256').replace('pose_picture_check','pose_picture_read_check').replace('run-picture.sh','run-input-read.sh')
# Existing picture review is reused verbatim for the numerical/lifecycle gate.
# New Host/read tests are verified by a separate reviewer before contracts.
fresh('tools/pose-v1/review_input_read.py',review)
runner=read('tools/pose-v1/run-picture.sh').replace('picture_binary_sha256','read_picture_binary_sha256').replace('pose_picture_check','pose_picture_read_check')
needle='    for name in pose_picture_source_selftest'
runner=runner.replace(needle,'    for name in pose_input_read_selftest pose_input_read_sdk_selftest pose_input_read_host_check pose_picture_source_selftest',1)
runner=runner.replace('        case "$name" in *producer*)','        case "$name" in *sdk_selftest) set -- "$work/$name" "$work/package/graph/piw24_ZG.json";; *host_check) set -- "$work/$name" --graph "$work/package/graph/piw24_ZG.json" --fixtures "$work/package/fixtures" --output "$run/host";; *producer*)',1)
runner=runner.replace('        timeout --signal=TERM --kill-after=5s 10s "$@"','        budget=10\n        if test "$name" = pose_input_read_host_check; then budget=300; fi\n        timeout --signal=TERM --kill-after=5s "$budget" "$@"',1)
fresh('tools/pose-v1/run-input-read.sh',runner)
base=root/'.local/pose-v1-picture/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
m['input_read_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
m['build_files'].pop('tools/pose-v1/picture-CMakeLists.txt')
m['build_files']['tools/pose-v1/input-read-CMakeLists.txt']=dict(destination='CMakeLists.txt',sha256=g.sha(root/'tools/pose-v1/input-read-CMakeLists.txt'))
for folder,names in [('include',['input_read_contract.hpp','input_read_sdk.hpp']),('src',['input_read_contract.cpp','input_read_sdk.cpp','input_read_selftest.cpp','input_read_sdk_selftest.cpp','input_read_host_check.cpp','read_input_bridge.cpp'])]:
    for name in names:
        rel='software/pose_v1/'+folder+'/'+name;m['build_files'][rel]=dict(destination=name,sha256=g.sha(root/rel))
for name in ['create_input_read_candidate.py','Build-InputRead.ps1','run-input-read.sh','review_input_read_build_base.py','review_input_read.py','review_input_read_contracts.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-InputRead.ps1'
m['input_read']=dict(device_inputs='Tensor::read into owned Host CPTR',host_inputs='original copyFrom',output_writeback='original copyFrom',zero_copy=False,shared_source_region_with_copy=True,extra_normal_source_reads=False)
out=root/'.local/pose-v1-input-read/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
