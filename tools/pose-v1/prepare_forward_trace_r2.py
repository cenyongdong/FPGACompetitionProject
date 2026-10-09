"""Create isolated pure-timing/failure-only sources and identity-bound package."""
from pathlib import Path
import json,shutil
import mixed_validation_gate as old
root=old.ROOT
def put(rel,text):
    p=root/rel;assert not p.exists(),p;p.write_text(text,encoding='utf-8',newline='\n')
header=(root/'software/pose_v1/include/application_core.hpp').read_text(encoding='utf-8')
assert header.count('size_t diagnostic_frames=4;')==1
put('software/pose_v1/include/trace_application_core_r2.hpp',header.replace('size_t diagnostic_frames=4;','size_t diagnostic_frames=4;\n    size_t timing_frames=0;'))
core=(root/'software/pose_v1/src/application_core.cpp').read_text(encoding='utf-8')
assert core.count('fc::sample_limit=c.diagnostic_frames;')==1
put('software/pose_v1/src/trace_application_core_r2.cpp',core.replace('fc::sample_limit=c.diagnostic_frames;','need(c.timing_frames<=32,"Timing sampling is bounded to32 frames");\n        fc::sample_limit=c.timing_frames?c.timing_frames:c.diagnostic_frames;'))
bridge=(root/'software/pose_v1/src/application_bridge.cpp').read_text(encoding='utf-8').replace('#include "mixed_bridge.hpp"','#include "mixed_bridge.hpp"\n#include "host_failure_evidence.hpp"\n#include <cstring>\n#include <sstream>')
needle='auto compute=Clock::now();auto computed=cpu::forward(op,staged,{});';assert bridge.count(needle)==1
replacement='''auto compute=Clock::now();std::vector<xrt::Tensor> computed;
    try{computed=cpu::forward(op,staged,{});}catch(const std::exception& error){
        // Successful path unchanged. All snapshots own bytes from existing Host staging.
        if(pose::failure_evidence::enabled())try{
            std::vector<pose::failure_evidence::Blob> blobs;
            for(size_t i=0;i<staged.size();++i){const auto& t=staged[i];
                need(host(t)&&t.dtype()->element_dtype.isFP32(),"capture","Failure input must be Host CPTR FP32");
                bounds(t,t.dtype(),"capture");const auto bytes=t.dtype().bytes();
                need(bytes>0&&bytes<=1024*1024,"capture","Failure input byte bound");
                pose::failure_evidence::Blob b;b.slot=i;b.offset=t.offset();b.chunkBytes=t.chunk()->byte_size;
                for(int64_t d:t.dtype()->shape)b.shape.push_back(d);
                for(size_t a=0;a<t.dtype()->shape.size();++a)b.layout+=t.dtype()->layout.getAxisCharName(int64_t(a));
                b.distributions=t.dtype()->merged_distrs.size();b.bytes.resize(size_t(bytes));
                std::memcpy(b.bytes.data(),t.data().cptr(),size_t(bytes));blobs.push_back(std::move(b));
            }
            std::ostringstream declarations;declarations<<'[';size_t slot=0;
            for(const auto& v:op->inputs){if(slot)declarations<<',';
                declarations<<"{\\"slot\\":"<<slot++<<",\\"parameter\\":"<<(v.isParams()?"true":"false")<<",\\"bytes\\":"<<v.tensorType().bytes()<<",\\"shape\\":[";
                for(size_t j=0;j<v.tensorType()->shape.size();++j){if(j)declarations<<',';declarations<<v.tensorType()->shape[j];}declarations<<"]}";
            }
            declarations<<']';pose::failure_evidence::save(frame_id,invocation_id,op->op_id,error.what(),blobs,declarations.str());
        }catch(const std::exception& e){pose::failure_evidence::noteCaptureError(e.what());}
        catch(...){pose::failure_evidence::noteCaptureError("Unknown failure capture error");}
        throw; // Preserve the original CPU exception, never recover/retry or edit indices.
    }'''
put('software/pose_v1/src/trace_application_bridge_r2.cpp',bridge.replace(needle,replacement))
entry=(root/'software/pose_v1/src/forward_trace_check.cpp').read_text(encoding='utf-8').replace('#include "pipeline_fixture_source.hpp"','#include "pipeline_fixture_source.hpp"\n#include "host_failure_evidence.hpp"\nvoid host_failure_adapter_test(const std::filesystem::path&,const std::filesystem::path&);')
entry=entry.replace('proof::validatedHostGate(package,out);','proof::validatedHostGate(package,out);host_failure_adapter_test(package,out);')
entry=entry.replace('cfg.diagnostic_frames=mode=="trace-5hz"?32:0;','cfg.diagnostic_frames=0;cfg.timing_frames=mode=="trace-5hz"?32:0;\n        pose::failure_evidence::configure(out/"failed-host-inputs");')
put('software/pose_v1/src/forward_trace_check_r2.cpp',entry)
cm=(root/'tools/pose-v1/forward-trace-CMakeLists.txt').read_text(encoding='utf-8').replace('application_core.cpp application_bridge.cpp','application_core.cpp application_bridge.cpp host_failure_evidence.cpp host_failure_adapter_test.cpp')
cm+='\nadd_executable(pose_failure_evidence_selftest host_failure_evidence_selftest.cpp host_failure_evidence.cpp)\ntarget_include_directories(pose_failure_evidence_selftest PRIVATE .)\ntarget_link_libraries(pose_failure_evidence_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_failure_evidence_selftest PRIVATE -Wall -Wextra -Wpedantic)\n'
put('tools/pose-v1/forward-trace-r2-CMakeLists.txt',cm)
builder=(root/'tools/pose-v1/Build-ForwardTrace.ps1').read_text(encoding='utf-8').replace('mixed-20261008-forward-trace-r1','mixed-20261009-forward-trace-r2')
builder=builder.replace("'pose_display_process_selftest','--parallel'","'pose_display_process_selftest','pose_failure_evidence_selftest','--parallel'")
builder=builder.replace("$poseHashes = [ordered]@{}","Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_failure_evidence_selftest'),(Join-Path $poseOutput 'pose_failure_evidence_selftest'))\n$poseHashes = [ordered]@{}")
builder=builder.replace("stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    failure_evidence_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_failure_evidence_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-ForwardTraceR2.ps1',builder)
runner=(root/'tools/pose-v1/run-forward-trace.sh').read_text(encoding='utf-8')
needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then';assert runner.count(needle)==1
runner=runner.replace(needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_failure_evidence_selftest" "$run/pose_failure_evidence_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_failure_evidence_selftest" "$run/failure-evidence-contracts" > "$run/failure-evidence.stdout.log" 2> "$run/failure-evidence.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/failure-evidence.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-forward-trace-r2.sh',runner)
review=(root/'tools/pose-v1/review_forward_stage.py').read_text(encoding='utf-8').replace('Build-ForwardTrace.ps1','Build-ForwardTraceR2.ps1').replace('run-forward-trace.sh','run-forward-trace-r2.sh')
review=review.replace("('timing_frozen_parent','display_frozen_parent')","('timing_frozen_parent','display_frozen_parent','trace_frozen_parent','trace_r2_frozen_sources')")
review=review.replace("('pose_display_worker','display_worker_sha256')","('pose_failure_evidence_selftest','failure_evidence_selftest_sha256'),('pose_display_worker','display_worker_sha256')")
review=review.replace("'timing-contracts','display-contracts')","'timing-contracts','display-contracts','failure-evidence')")
review=review.replace("assert not (r/'display-contracts/normal/child.stderr.log').read_bytes()",'''assert not (r/'display-contracts/normal/child.stderr.log').read_bytes()
            assert load(r/'failure-evidence.stdout.log')==dict(status='passed',rejections=9,owned_FP32_bytes=16,SDK_device=False)
            assert load(out/'failure-probe.json')==dict(status='passed',op_id=192,original_rejection_preserved=True,Host_staged_bytes_match=True,device_opened=False)
            probe=load(out/'failed-host-inputs/failure.json');assert probe['op_id']==192 and probe['frame_id']==42 and not probe['device_read']
            for t in probe['inputs']:
                v=np.fromfile(out/'failed-host-inputs'/t['file'],dtype='<f4');assert len(v)*4==t['bytes']
                assert (v[0]==0.5 and (v[1:]==0).all()) if t['slot']==1 else (v==0).all()
            assert not (out/'failed-host-inputs/capture-error.txt').exists()''')
put('tools/pose-v1/review_forward_r2_stage.py',review)
base=root/'.local/pose-v1-forward-trace/package-20261008-r1';old.verify(base);m=old.load(base/'manifest.json')
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
replace={
'software/pose_v1/include/application_core.hpp':'software/pose_v1/include/trace_application_core_r2.hpp',
'software/pose_v1/src/application_core.cpp':'software/pose_v1/src/trace_application_core_r2.cpp',
'software/pose_v1/src/application_bridge.cpp':'software/pose_v1/src/trace_application_bridge_r2.cpp',
'software/pose_v1/src/forward_trace_check.cpp':'software/pose_v1/src/forward_trace_check_r2.cpp',
'tools/pose-v1/forward-trace-CMakeLists.txt':'tools/pose-v1/forward-trace-r2-CMakeLists.txt'}
m['trace_r2_frozen_sources']={rel:old.sha(root/rel) for rel in replace}
for before,after in replace.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=old.sha(root/after))
for rel in ('include/host_failure_evidence.hpp','src/host_failure_evidence.cpp','src/host_failure_adapter_test.cpp','src/host_failure_evidence_selftest.cpp'):
    source='software/pose_v1/'+rel;m['build_files'][source]=dict(destination=Path(rel).name,sha256=old.sha(root/source))
for name in ('prepare_forward_trace_r2.py','Build-ForwardTraceR2.ps1','run-forward-trace-r2.sh','review_forward_r2_stage.py'):
    rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ForwardTraceR2.ps1';m['forward_trace'].update(existing_Engine_and_bridge_unchanged=False,pure_timing_without_readiness_queries=True,failure_capture_only=True,normal_copy_math_wait_unchanged=True)
out=root/'.local/pose-v1-forward-trace/package-20261009-r2';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(old.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(json.dumps(dict(payloads=old.verify(out),build_sources=len(m['build_files']))))
