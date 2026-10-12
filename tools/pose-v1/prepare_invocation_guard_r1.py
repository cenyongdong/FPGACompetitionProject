"""Isolated post-copy observer and independent persistence integration."""
import json, shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def read(rel): return (root/rel).read_text(encoding='utf-8')
def put(rel,text):
    p=root/rel; assert not p.exists(),p
    p.write_text(text,encoding='utf-8',newline='\n')
def change(text,a,b):
    assert text.count(a)==1,(a,text.count(a))
    return text.replace(a,b)
base=root/'.local/pose-v1-stage-guard/package-20261009-r1';g.verify(base)
m=g.load(base/'manifest.json')
header=change(read('software/pose_v1/include/host_stage_observation.hpp'),
 'void configure(const std::filesystem::path& freshRoot);',
 'using CopyObserver=std::function<void(uint64_t,uint64_t,int64_t,size_t,std::vector<char>)>;\nvoid configure(const std::filesystem::path& freshRoot,CopyObserver observer={});')
put('software/pose_v1/include/invocation_stage_observation.hpp',header)
source=read('software/pose_v1/src/host_stage_observation.cpp')
source=change(source,'std::filesystem::path root;bool configured=false;', 'CopyObserver observer;std::filesystem::path root;bool configured=false;')
source=change(source,'void configure(const std::filesystem::path& path)', 'void configure(const std::filesystem::path& path,CopyObserver callback)')
source=change(source,'root=path;configured=true;', 'root=path;observer=std::move(callback);configured=true;')
source=change(source,'append(s.str());entries_.push_back(std::move(e));',
 'append(s.str());\n    // Observe owned shadow bytes; never reread the staging pointer.\n    if(observer)observer(frame_,invocation_,op_,e.info.slot,e.bytes);\n    entries_.push_back(std::move(e));')
put('software/pose_v1/src/invocation_stage_observation.cpp',source)
entry=read('software/pose_v1/src/stage_guard_check_r1.cpp')
entry=change(entry,'#include "host_stage_observation.hpp"','#include "host_stage_observation.hpp"\n#include "invocation_evidence.hpp"')
entry=change(entry,'host_failure_adapter_test(package,out);pose::stage_observation::saveMetadata();','host_failure_adapter_test(package,out);')
entry=change(entry,'bool firstCapture=false;', 'auto hostFrame=std::make_shared<pose::invocation_evidence::Frame>();\n    bool firstCapture=false;')
entry=change(entry,'pose::stage_observation::configure(out/"copy-observations");', '''pose::stage_observation::configure(out/"copy-observations",[hostFrame](uint64_t frame,uint64_t invocation,int64_t op,size_t slot,std::vector<char> bytes){
            hostFrame->begin(frame,invocation);hostFrame->record(op,slot,std::move(bytes));
        });''')
entry=change(entry,'}catch(...){fail(std::current_exception());if(engine)try{engine->save_evidence();}catch(...){}}','}catch(...){fail(std::current_exception());}')
entry=change(entry,'''    try{
        pose::measurement::save(measured,cases,out);if(engine)engine->save_evidence();pose::stage_observation::saveMetadata();
        proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());
        load::saveFrameReferences(measured,cases,out);
    }catch(...){if(!failure)failure=std::current_exception();}''', '''    const bool failedBeforeFlush=bool(failure);
    pose::invocation_evidence::flush({
        {"complete-results",[&]{pose::measurement::save(measured,cases,out);}},
        {"copy-metadata",[&]{pose::stage_observation::saveMetadata();}},
        {"Engine-evidence",[&]{if(engine)engine->save_evidence();}},
        {"failed-Host-frame",[&]{if(failedBeforeFlush&&hostFrame->inputs())hostFrame->save(out/"failed-invocation-inputs");}},
        {"warmup",[&]{proof::persistBytes(out/"frames/warmup.nv12",warm.nv12.data(),warm.nv12.size());}},
        {"ARM-frame-references",[&]{load::saveFrameReferences(measured,cases,out);}}
    },failure,out/"persistence-ledger.json");''')
put('software/pose_v1/src/invocation_guard_check_r1.cpp',entry)
probe=read('software/pose_v1/src/stage_guard_host_probe_r1.cpp')
probe=change(probe,'#include "host_stage_observation.hpp"','#include "host_stage_observation.hpp"\n#include "invocation_evidence.hpp"\n#include <memory>')
probe=change(probe,'pose::stage_observation::configure(out/"copy-observations");','''auto frame=std::make_shared<pose::invocation_evidence::Frame>();
    pose::stage_observation::configure(out/"copy-observations",[frame](uint64_t id,uint64_t invocation,int64_t opId,size_t slot,std::vector<char> bytes){
        frame->begin(id,invocation);frame->record(opId,slot,std::move(bytes));
    });''')
probe += '''
'''
needle='    std::ofstream f(out/"failure-probe.json");'
assert probe.count(needle)==1
probe=probe.replace(needle,'''    // Real Host forward succeeds; a later full-result gate is deliberately rejected.
    for(size_t i=0;i<inputs.size();++i){std::fill(values[i].begin(),values[i].end(),0.0f);
        inputs[i].write(0,reinterpret_cast<char*>(values[i].data()),values[i].size()*4);}
    pose_v1::mixed_candidate::set_frame(43,1);
    auto result=pose_v1::mixed_candidate::forward(op,inputs,{});
    if(result.empty()||frame->inputs()!=2||frame->bytes()!=47040)throw std::runtime_error("Finite Host probe coverage differs");
    // Release actual SDK inputs/results before persisting the independently owned copy.
    inputs.clear();result.clear();values.clear();
    auto original=std::make_exception_ptr(std::runtime_error("Synthetic final complete-output rejection"));bool tail=false;
    pose::invocation_evidence::flush({
        {"complete-results",[]{throw std::runtime_error("Repeated complete-output rejection");}},
        {"failed-Host-frame",[&]{frame->save(out/"finite-output-probe");}},
        {"copy-metadata",[]{pose::stage_observation::saveMetadata();}},
        {"remaining-evidence",[&]{tail=true;}}
    },original,out/"finite-output-ledger.json");
    bool preserved=false;try{std::rethrow_exception(original);}catch(const std::runtime_error& e){preserved=std::string(e.what())=="Synthetic final complete-output rejection";}
    if(!preserved||!tail)throw std::runtime_error("Final rejection persistence blocked or replaced");
    for(size_t i=0;i<2;++i){std::ifstream owned(out/"finite-output-probe"/("op192.slot"+std::to_string(i)+".f32"),std::ios::binary);
        std::vector<char> blob(size_t(op->inputs[i].tensorType().bytes()));owned.read(blob.data(),blob.size());
        if(!owned||std::any_of(blob.begin(),blob.end(),[](char c){return c!=0;}))throw std::runtime_error("Released Host probe owned bytes differ");}
    std::ofstream contract(out/"finite-output-probe.json");contract<<"{\\"status\\":\\"passed\\",\\"Host_forward_completed\\":true,\\"owned_inputs\\":2,\\"owned_bytes\\":47040,\\"original_error_preserved\\":true,\\"source_device_read\\":false}\\n";
'''+needle)
put('software/pose_v1/src/invocation_guard_host_probe_r1.cpp',probe)
cm=change(read('tools/pose-v1/stage-guard-CMakeLists.txt'),'failure_source_readback.cpp host_stage_observation.cpp mixed_host_check.cpp','failure_source_readback.cpp host_stage_observation.cpp invocation_evidence.cpp mixed_host_check.cpp')
cm+='\nadd_executable(pose_invocation_evidence_selftest invocation_evidence_selftest.cpp invocation_evidence.cpp)\ntarget_include_directories(pose_invocation_evidence_selftest PRIVATE .)\ntarget_link_libraries(pose_invocation_evidence_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_invocation_evidence_selftest PRIVATE -Wall -Wextra -Wpedantic -Werror)\n'
put('tools/pose-v1/invocation-guard-CMakeLists.txt',cm)
builder=read('tools/pose-v1/Build-StageGuard.ps1').replace('mixed-20261009-stage-guard-r1','mixed-20261009-invocation-guard-r1')
builder=change(builder,"'pose_stage_observation_selftest','--parallel'","'pose_stage_observation_selftest','pose_invocation_evidence_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_invocation_evidence_selftest'),(Join-Path $poseOutput 'pose_invocation_evidence_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    invocation_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_invocation_evidence_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-InvocationGuard.ps1',builder)
runner=read('tools/pose-v1/run-stage-guard.sh')
needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
runner=change(runner,needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_invocation_evidence_selftest" "$run/pose_invocation_evidence_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_invocation_evidence_selftest" "$run/invocation-contracts" > "$run/invocation-contracts.stdout.log" 2> "$run/invocation-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/invocation-contracts.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-invocation-guard.sh',runner)
review=read('tools/pose-v1/review_stage_guard.py').replace('Build-StageGuard.ps1','Build-InvocationGuard.ps1').replace('run-stage-guard.sh','run-invocation-guard.sh')
review=change(review,"'stage_guard_frozen_sources')","'stage_guard_frozen_sources','invocation_guard_frozen_sources')")
put('tools/pose-v1/review_invocation_guard.py',review)
mapping={'software/pose_v1/src/stage_guard_check_r1.cpp':'software/pose_v1/src/invocation_guard_check_r1.cpp','software/pose_v1/src/stage_guard_host_probe_r1.cpp':'software/pose_v1/src/invocation_guard_host_probe_r1.cpp','software/pose_v1/include/host_stage_observation.hpp':'software/pose_v1/include/invocation_stage_observation.hpp','software/pose_v1/src/host_stage_observation.cpp':'software/pose_v1/src/invocation_stage_observation.cpp','tools/pose-v1/stage-guard-CMakeLists.txt':'tools/pose-v1/invocation-guard-CMakeLists.txt'}
m['invocation_guard_frozen_sources']={rel:g.sha(root/rel) for rel in mapping}
for before,after in mapping.items():
    item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
for rel in ['include/invocation_evidence.hpp','src/invocation_evidence.cpp','src/invocation_evidence_selftest.cpp']:
    full='software/pose_v1/'+rel;m['build_files'][full]=dict(destination=Path(rel).name,sha256=g.sha(root/full))
for name in ['prepare_invocation_guard_r1.py','Build-InvocationGuard.ps1','run-invocation-guard.sh','review_invocation_guard.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-InvocationGuard.ps1'
m['invocation_guard']=dict(observer_source='existing_owned_post_copy_shadow',normal_device_reads_added=0,frame_maximum_bytes=1048576,frame_maximum_inputs=8,independent_persistence_tasks=6,original_exception_preserved=True)
out=root/'.local/pose-v1-invocation-guard/package-20261009-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
