"""New isolated object observation; no modification of frozen bridge or math."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
base=root/'.local/pose-v1-producer-count/package-20261009-r2';g.verify(base);m=g.load(base/'manifest.json')
bridge=change(read('software/pose_v1/src/producer_count_bridge_r2.cpp'),'#include "producer_count_observation.hpp"','#include "producer_count_observation.hpp"\n#include "tensor_identity_observation.hpp"')
adapter=r'''std::string identityType(const xir::TensorType& type){
    std::ostringstream f;f<<"{\"FP32\":"<<(type->element_dtype.isFP32()?"true":"false")<<",\"bytes\":"<<type.bytes()<<",\"shape\":[";
    for(size_t i=0;i<type->shape.size();++i){if(i)f<<',';f<<type->shape[i];}f<<"],\"layout\":\"";
    for(size_t i=0;i<type->shape.size();++i)f<<type->layout.getAxisCharName(int64_t(i));f<<"\",\"distributions\":[";
    bool first=true;for(const auto& d:type->merged_distrs){if(!first)f<<',';first=false;f<<"{\"uvalue\":"<<int(d->uvalue)<<",\"axes\":[";bool a=true;for(auto axis:d->merged_axis){if(!a)f<<',';a=false;f<<axis;}f<<"],\"valid_mask\":\"";for(bool bit:d->valid_mask)f<<(bit?'1':'0');f<<"\"}";}f<<"]}";return f.str();
}
pose::tensor_identity::Storage identityStorage(const xrt::Tensor&t,const xir::TensorType&declared){
    pose::tensor_identity::Storage s;s.tensor=reinterpret_cast<uintptr_t>(t.operator->());s.region=reinterpret_cast<uintptr_t>(t.memRegion().operator->());s.chunk=reinterpret_cast<uintptr_t>(t.chunk().operator->());s.device=reinterpret_cast<uintptr_t>(t.memRegion().device().operator->());
    s.offset=t.offset();s.capacity=t.chunk()->byte_size;s.bytes=t.dtype().bytes();s.declaredMatches=t.dtype()==declared;s.ownerMatches=host(t)||(allowed_device.defined()&&t.memRegion().device().same_as(allowed_device));
    auto kind=t.data().ptype();s.kind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";s.address=kind==xrt::PtrType::CPTR?reinterpret_cast<uintptr_t>(t.data().cptr()):t.data().addr();s.regionKey=std::string(t.memRegion()->typeKey());s.type=identityType(t.dtype());s.declaredType=identityType(declared);return s;
}
void observeIdentity(const xir::Operation&op,size_t slot,bool after,const xrt::Tensor&source,const xrt::Tensor&dest,const xir::TensorType&declared){
    if(!pose::tensor_identity::enabled())return;
    pose::tensor_identity::Pair pair;pair.source=identityStorage(source,declared);pair.destination=identityStorage(dest,declared);pair.sameRegion=source.memRegion().same_as(dest.memRegion());pair.sameDevice=source.memRegion().device().same_as(dest.memRegion().device());pose::tensor_identity::sample(frame_id,invocation_id,op->op_id,slot,after,std::move(pair));
}
'''
bridge=change(bridge,'template<class Op> void add() {',adapter+'\ntemplate<class Op> void add() {')
bridge=change(bridge,'const auto copyBegin=pose::stage_observation::now();','observeIdentity(op,index,false,src,dst,value.tensorType());\n        const auto copyBegin=pose::stage_observation::now();')
bridge=change(bridge,'observation.afterCopy(std::move(metadata),dst.data().cptr());','observation.afterCopy(std::move(metadata),dst.data().cptr());\n        observeIdentity(op,index,true,src,dst,value.tensorType());')
put('software/pose_v1/src/tensor_identity_bridge_r1.cpp',bridge)
entry=change(read('software/pose_v1/src/producer_count_check_r2.cpp'),'#include "producer_count_observation.hpp"','#include "producer_count_observation.hpp"\n#include "tensor_identity_observation.hpp"')
entry=change(entry,'pose::producer_count::configure(out/"producer-counts");','pose::producer_count::configure(out/"producer-counts");\n        pose::tensor_identity::configure(out/"tensor-identities");')
entry=change(entry,'{"192-producer-counts",[]{pose::producer_count::save();}},','{"192-producer-counts",[]{pose::producer_count::save();}},\n        {"tensor-object-identities",[]{pose::tensor_identity::save();}},')
put('software/pose_v1/src/tensor_identity_check_r1.cpp',entry)
cm=change(read('tools/pose-v1/producer-count-CMakeLists.txt'),'invocation_evidence.cpp producer_count_observation.cpp','invocation_evidence.cpp producer_count_observation.cpp tensor_identity_observation.cpp')
cm+='\nadd_executable(pose_tensor_identity_selftest tensor_identity_selftest.cpp tensor_identity_observation.cpp)\ntarget_include_directories(pose_tensor_identity_selftest PRIVATE .)\ntarget_link_libraries(pose_tensor_identity_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_tensor_identity_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)\n'
put('tools/pose-v1/tensor-identity-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-ProducerCount.ps1').replace('mixed-20261009-producer-count-r2','mixed-20261010-tensor-identity-r1')
builder=change(builder,"'pose_producer_count_selftest','--parallel'","'pose_producer_count_selftest','pose_tensor_identity_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_tensor_identity_selftest'),(Join-Path $poseOutput 'pose_tensor_identity_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    tensor_identity_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_tensor_identity_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-TensorIdentity.ps1',builder)
runner=change(read('tools/pose-v1/run-producer-count.sh'),'if test "$au_code" = 0; then\nif test "$stage" = host-check; then',r'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_tensor_identity_selftest" "$run/pose_tensor_identity_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_tensor_identity_selftest" "$run/identity-contracts" > "$run/identity-contracts.stdout.log" 2> "$run/identity-contracts.stderr.log"
    au_code=$?
    printf '%s\n' "$au_code" > "$run/identity-contracts.exit.txt"
fi
if test "$au_code" = 0; then
if test "$stage" = host-check; then''')
put('tools/pose-v1/run-tensor-identity.sh',runner)
review=read('tools/pose-v1/review_producer_count_stage.py').replace('Build-ProducerCount.ps1','Build-TensorIdentity.ps1').replace('run-producer-count.sh','run-tensor-identity.sh')
review=change(review,"'producer_count_frozen_sources')","'producer_count_frozen_sources','tensor_identity_frozen_sources')")
put('tools/pose-v1/review_tensor_identity_stage.py',review)
mapping={'software/pose_v1/src/producer_count_bridge_r2.cpp':'software/pose_v1/src/tensor_identity_bridge_r1.cpp','software/pose_v1/src/producer_count_check_r2.cpp':'software/pose_v1/src/tensor_identity_check_r1.cpp','tools/pose-v1/producer-count-CMakeLists.txt':'tools/pose-v1/tensor-identity-CMakeLists.txt'}
m['tensor_identity_frozen_sources']={p:g.sha(root/p) for p in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
for p in ('include/tensor_identity_observation.hpp','src/tensor_identity_observation.cpp','src/tensor_identity_selftest.cpp'):
    rel='software/pose_v1/'+p;m['build_files'][rel]=dict(destination=Path(p).name,sha256=g.sha(root/rel))
for name in ('prepare_tensor_identity_r1.py','Build-TensorIdentity.ps1','run-tensor-identity.sh','review_tensor_identity_stage.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-TensorIdentity.ps1';m['tensor_identity_observation']=dict(rows_limit=2048,bytes_limit=4194304,public_objects_only=True,normal_device_reads_added=0,wait_changed=False,copy_changed=False,original_error_capture_preserved=True)
out=root/'.local/pose-v1-tensor-identity/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
