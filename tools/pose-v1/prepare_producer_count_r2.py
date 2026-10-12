"""Isolated192 public-counter observations; original waits/copies unchanged."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(p):return (root/p).read_text(encoding='utf-8')
def change(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def put(p,s):p=root/p;assert not p.exists();p.write_text(s,encoding='utf-8',newline='\n')
base=root/'.local/pose-v1-invocation-guard/package-20261009-r1';g.verify(base);m=g.load(base/'manifest.json')
ops={v['op_id']:v for v in g.load(base/'graph/piw24_ZG.json')['ops']};producers={v['v_id']:op['op_id'] for op in ops.values() for v in op['outputs']}
sources=ops[192]['inputs'];assert [v['v_id'] for v in sources]==[4386,4390] and [producers[v['v_id']] for v in sources]==[8629,8631]
fusion=g.load(root/'tools/pose-v1/mixed-fusion-baseline.json');group=next(v for v in fusion['groups'] if v['effective_op_id']==9186)
assert group['sync_index']+group['layer_count']==234 and all(producers[v['v_id']] in group['members'] for v in sources)
bridge=change(read('software/pose_v1/src/stage_guard_bridge_r1.cpp'),'#include "host_stage_observation.hpp"','#include "host_stage_observation.hpp"\n#include "producer_count_observation.hpp"')
bridge=change(bridge,'template<class Op> void add() {','''void observe192(const xir::Operation& op,size_t slot,const xrt::Tensor& src,pose::producer_count::Point point){
    if(!permit_hardware||op->op_id!=192)return;
    const auto range=fusion_baseline::sync.at(9186);
    need(range.first+range.second==234,"producer","192 fusion end differs");
    const auto kind=src.data().ptype();pose::producer_count::Source source;
    source.producer=slot?8631:8629;source.bytes=src.dtype().bytes();source.offset=src.offset();source.capacity=src.chunk()->byte_size;
    source.kind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";
    source.region=std::string(src.memRegion()->typeKey());if(kind!=xrt::PtrType::CPTR)source.address=src.data().addr();
    pose::producer_count::sample(frame_id,invocation_id,slot,point,source,[&]{return allowed_device.cast<xrt::ZG330Device>().layerCount();});
}
template<class Op> void add() {''')
bridge=change(bridge,'auto begin=Clock::now();\n        {forward_clock::Span t("bridge.wait"','observe192(op,index,src,pose::producer_count::Point::BeforeWait);\n        auto begin=Clock::now();\n        {forward_clock::Span t("bridge.wait"')
bridge=change(bridge,'const auto waitEnd=pose::stage_observation::now();','const auto waitEnd=pose::stage_observation::now();\n        observe192(op,index,src,pose::producer_count::Point::AfterWait);')
bridge=change(bridge,'const auto copyBegin=pose::stage_observation::now();','observe192(op,index,src,pose::producer_count::Point::BeforeCopy);\n        const auto copyBegin=pose::stage_observation::now();')
bridge=change(bridge,'const auto copyEnd=pose::stage_observation::now();','const auto copyEnd=pose::stage_observation::now();\n        observe192(op,index,src,pose::producer_count::Point::AfterCopy);')
put('software/pose_v1/src/producer_count_bridge_r2.cpp',bridge)
entry=change(read('software/pose_v1/src/invocation_guard_check_r1.cpp'),'#include "invocation_evidence.hpp"','#include "invocation_evidence.hpp"\n#include "producer_count_observation.hpp"')
entry=change(entry,'pose::failure_evidence::configure(out/"failed-host-inputs");','pose::producer_count::configure(out/"producer-counts");\n        pose::failure_evidence::configure(out/"failed-host-inputs");')
entry=change(entry,'{"copy-metadata",[&]{pose::stage_observation::saveMetadata();}},','{"copy-metadata",[&]{pose::stage_observation::saveMetadata();}},\n        {"192-producer-counts",[]{pose::producer_count::save();}},')
put('software/pose_v1/src/producer_count_check_r2.cpp',entry)
cm=change(read('tools/pose-v1/invocation-guard-CMakeLists.txt'),'host_stage_observation.cpp invocation_evidence.cpp mixed_host_check.cpp','host_stage_observation.cpp invocation_evidence.cpp producer_count_observation.cpp mixed_host_check.cpp')
cm+='\nadd_executable(pose_producer_count_selftest producer_count_observation_selftest.cpp producer_count_observation.cpp)\ntarget_include_directories(pose_producer_count_selftest PRIVATE .)\ntarget_link_libraries(pose_producer_count_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_producer_count_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)\n'
put('tools/pose-v1/producer-count-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-InvocationGuard.ps1').replace('mixed-20261009-invocation-guard-r1','mixed-20261009-producer-count-r2')
builder=change(builder,"'pose_invocation_evidence_selftest','--parallel'","'pose_invocation_evidence_selftest','pose_producer_count_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_producer_count_selftest'),(Join-Path $poseOutput 'pose_producer_count_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    producer_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_producer_count_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-ProducerCount.ps1',builder)
runner=read('tools/pose-v1/run-invocation-guard.sh');needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
runner=change(runner,needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_producer_count_selftest" "$run/pose_producer_count_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_producer_count_selftest" "$run/producer-contracts" > "$run/producer-contracts.stdout.log" 2> "$run/producer-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/producer-contracts.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-producer-count.sh',runner)
review=read('tools/pose-v1/review_invocation_guard.py').replace('Build-InvocationGuard.ps1','Build-ProducerCount.ps1').replace('run-invocation-guard.sh','run-producer-count.sh')
review=change(review,"'invocation_guard_frozen_sources')","'invocation_guard_frozen_sources','producer_count_frozen_sources')")
put('tools/pose-v1/review_producer_count_stage.py',review)
mapping={'software/pose_v1/src/stage_guard_bridge_r1.cpp':'software/pose_v1/src/producer_count_bridge_r2.cpp','software/pose_v1/src/invocation_guard_check_r1.cpp':'software/pose_v1/src/producer_count_check_r2.cpp','tools/pose-v1/invocation-guard-CMakeLists.txt':'tools/pose-v1/producer-count-CMakeLists.txt'}
m['producer_count_frozen_sources']={p:g.sha(root/p) for p in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
for p in ['include/producer_count_observation.hpp','src/producer_count_observation.cpp','src/producer_count_observation_selftest.cpp']:
    rel='software/pose_v1/'+p;m['build_files'][rel]=dict(destination=Path(p).name,sha256=g.sha(root/rel))
for name in ['prepare_producer_count_r2.py','Build-ProducerCount.ps1','run-producer-count.sh','review_producer_count_stage.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ProducerCount.ps1'
m['producer_count_observation']=dict(op_id=192,source_values=[4386,4390],source_producers=[8629,8631],group=9186,target=234,points=['before_wait','after_wait','before_copy','after_copy'],maximum_queries_per_call=8,maximum_rows=824,normal_device_data_reads_added=0,wait_added=False,original_582_guard_unchanged=True)
out=root/'.local/pose-v1-producer-count/package-20261009-r2';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
