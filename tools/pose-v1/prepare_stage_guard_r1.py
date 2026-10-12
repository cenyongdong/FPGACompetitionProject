"""New snapshot + fresh group-completion candidate; old failed103 stays frozen."""
import json,shutil
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def put(rel,text):
    p=root/rel;assert not p.exists(),p;p.write_text(text,encoding='utf-8',newline='\n')
def change(text,before,after,count=1):
    assert text.count(before)==count,(before,text.count(before));return text.replace(before,after)
base=root/'.local/pose-v1-bounded-load/package-20261009-r2';g.verify(base);m=g.load(base/'manifest.json')
model=g.load(base/'graph/piw24_ZG.json');fusion=g.load(root/'tools/pose-v1/mixed-fusion-baseline.json');assert g.sha(base/'graph/piw24_ZG.json')==fusion['graph_sha256']
ops={x['op_id']:x for x in model['ops']};producers={v['v_id']:x['op_id'] for x in model['ops'] for v in x['outputs']}
group=next(x for x in fusion['groups'] if x['effective_op_id']==9189);assert group['sync_index']==481 and group['layer_count']==157
sources=[v for v in ops[582]['inputs'] if v['_type_key']!='icraft::xir::Params'];assert [producers[v['v_id']] for v in sources]==[8130,8131] and all(producers[v['v_id']] in group['members'] for v in sources)
def ancestors(oid,visited=None):
    visited=set() if visited is None else visited
    for v in ops[oid]['inputs']:
        prev=producers.get(v['v_id'])
        if prev is not None and prev not in visited:visited.add(prev);ancestors(prev,visited)
    return visited
assert all(582 not in ancestors(oid) for oid in group['members'])
bridge=(root/'software/pose_v1/src/source_application_bridge_r4.cpp').read_text(encoding='utf-8')
bridge=change(bridge,'#include "failure_source_readback.hpp"','#include "failure_source_readback.hpp"\n#include "host_stage_observation.hpp"\n#include "mixed_fusion_baseline.hpp"\n#include <icraft-xrt/dev/zg330_device.h>')
bridge=change(bridge,'std::vector<xrt::Tensor> staged;','std::vector<xrt::Tensor> staged;\n    pose::stage_observation::Call observation(frame_id,invocation_id,op->op_id);')
needle='auto allocate=Clock::now();auto dst=xrt::Tensor(value.tensorType()).mallocOn(xrt::HostDevice::MemRegion());'
extra='''const auto waitEnd=pose::stage_observation::now();
        if(permit_hardware&&op->op_id==582&&index==0){
            // A fresh SDK execution-counter poll, not a DMA/cache fence.
            const auto range=fusion_baseline::sync.at(9189),last=fusion_baseline::sync.at(9191);
            try{auto result=pose::stage_observation::waitFresh(uint32_t(range.first+range.second),uint32_t(last.first+last.second),[&]{return allowed_device.cast<xrt::ZG330Device>().layerCount();},std::chrono::milliseconds(10000));
                pose::stage_observation::recordCompletion(frame_id,invocation_id,op->op_id,result);
            }catch(const std::exception& e){pose::stage_observation::recordSyncFailure(frame_id,invocation_id,op->op_id,e.what());throw;}
        }
        '''
bridge=change(bridge,needle,extra+needle)
needle='{forward_clock::Span t("bridge.copy",op->op_id,index);dst.copyFrom(0,src,0,value.tensorType().bytes());}'
bridge=change(bridge,needle,'''const auto copyBegin=pose::stage_observation::now();
        '''+needle+'''
        const auto copyEnd=pose::stage_observation::now();
        pose::stage_observation::Info metadata;metadata.slot=index;metadata.bytes=size_t(value.tensorType().bytes());
        metadata.sourceOffset=src.offset();metadata.sourceCapacity=src.chunk()->byte_size;metadata.sourceRegion=std::string(src.memRegion()->typeKey());
        const auto kind=src.data().ptype();metadata.sourceKind=kind==xrt::PtrType::CPTR?"CPTR":kind==xrt::PtrType::ADDR?"ADDR":"BOTH";if(kind!=xrt::PtrType::CPTR)metadata.sourceAddress=src.data().addr();
        metadata.hostPointer=reinterpret_cast<uintptr_t>(dst.data().cptr());metadata.hostChunk=reinterpret_cast<uintptr_t>(dst.chunk().operator->());metadata.hostOffset=dst.offset();metadata.hostCapacity=dst.chunk()->byte_size;metadata.hostRegion=std::string(dst.memRegion()->typeKey());
        metadata.waitBegin=std::chrono::duration_cast<std::chrono::nanoseconds>(begin.time_since_epoch()).count();metadata.waitEnd=waitEnd;metadata.copyBegin=copyBegin;metadata.copyEnd=copyEnd;
        observation.afterCopy(std::move(metadata),dst.data().cptr());''')
bridge=change(bridge,'try{computed=cpu::forward(op,staged,{});}','try{observation.validate();computed=cpu::forward(op,staged,{});}')
bridge=change(bridge,'if(pose::failure_evidence::enabled())try{','const auto errorTime=pose::stage_observation::now();\n        if(pose::failure_evidence::enabled())try{')
needle="declarations<<']';pose::failure_evidence::save(frame_id,invocation_id,op->op_id,error.what(),blobs,declarations.str());"
bridge=change(bridge,needle,needle+'\n            observation.saveFailure(pose::failure_evidence::directory(),errorTime);')
# The old evidence interface exposes no directory accessor; use this module's root sibling.
bridge=bridge.replace('pose::failure_evidence::directory()','pose::stage_observation::failureRoot()')
put('software/pose_v1/src/stage_guard_bridge_r1.cpp',bridge)
probe=(root/'software/pose_v1/src/source_failure_adapter_test_r4.cpp').read_text(encoding='utf-8')
probe=change(probe,'#include "mixed_bridge.hpp"','#include "mixed_bridge.hpp"\n#include "host_stage_observation.hpp"')
probe=change(probe,'pose::failure_evidence::configure(out/"failed-host-inputs");','pose::stage_observation::configure(out/"copy-observations");\n    pose::failure_evidence::configure(out/"failed-host-inputs");')
put('software/pose_v1/src/stage_guard_host_probe_r1.cpp',probe)
entry=(root/'software/pose_v1/src/bounded_load_check_r1.cpp').read_text(encoding='utf-8')
entry=change(entry,'#include "failure_source_readback.hpp"','#include "failure_source_readback.hpp"\n#include "host_stage_observation.hpp"')
entry=change(entry,'host_failure_adapter_test(package,out);','host_failure_adapter_test(package,out);pose::stage_observation::saveMetadata();')
entry=change(entry,'pose::failure_evidence::configure(out/"failed-host-inputs");','pose::stage_observation::configure(out/"copy-observations");\n        pose::failure_evidence::configure(out/"failed-host-inputs");')
entry=change(entry,'pose::measurement::save(measured,cases,out);if(engine)engine->save_evidence();','pose::measurement::save(measured,cases,out);if(engine)engine->save_evidence();pose::stage_observation::saveMetadata();')
entry=change(entry,'pose::measurement::TimedWindowInput input;','pose::measurement::TimedWindowInput input(out);')
entry=change(entry,'record.processEnd=ns();','record.processEnd=ns();input.markReturned();')
put('software/pose_v1/src/stage_guard_check_r1.cpp',entry)
# Extend only the transport-owned interface; implementation still owns its join.
h=(root/'software/pose_v1/include/tcp_receiver.hpp').read_text(encoding='utf-8');h=change(h,'void stop();void check();','Stats stopAndStats();\n    void stop();void check();')
put('software/pose_v1/include/stage_guard_tcp_receiver.hpp',h)
tcp=(root/'software/pose_v1/src/tcp_receiver.cpp').read_text(encoding='utf-8');tcp+='\nnamespace pose_v1::transport { Stats Receiver::stopAndStats(){p_->stop();if(p_->worker.joinable())p_->worker.join();return stats();} }\n'
put('software/pose_v1/src/stage_guard_tcp_receiver.cpp',tcp)
inp=(root/'software/pose_v1/include/process_window_input.hpp').read_text(encoding='utf-8');inp=change(inp,'size_t consumed_=0;','size_t consumed_=0,returned_=0;std::filesystem::path evidence_;bool saved_=false;\n    void saveStats(bool failure);')
inp=change(inp,'TimedWindowInput();','explicit TimedWindowInput(const std::filesystem::path&);\n    ~TimedWindowInput();\n    void markReturned(){++returned_;}')
put('software/pose_v1/include/stage_guard_window_input.hpp',inp)
source=(root/'software/pose_v1/src/process_window_input.cpp').read_text(encoding='utf-8')
source=change(source,'TimedWindowInput::TimedWindowInput():receiver_("192.168.126.49",39001,5000,1)','TimedWindowInput::TimedWindowInput(const std::filesystem::path& out):receiver_("192.168.126.49",39001,5000,1),evidence_(out)')
source=change(source,'receiver_.stop();receiver_.check();const auto s=receiver_.stats();','const auto s=receiver_.stopAndStats();receiver_.check();')
source=change(source,'f.close();\n    if(!f','f.close();saved_=true;\n    if(!f')
source=change(source,'<<s.reconnect_discarded<<"}\\n"','<<s.reconnect_discarded<<",\\"returned\\":"<<returned_<<",\\"final_after_join\\":true,\\"failure_path\\":false}\\n"')
source+='''
namespace pose::measurement {
void TimedWindowInput::saveStats(bool failure){const auto s=receiver_.stopAndStats();std::ofstream f(evidence_/"input-summary.json");
    f<<"{\\"sessions\\":"<<s.sessions<<",\\"received\\":"<<s.received<<",\\"consumed\\":"<<consumed_<<",\\"returned\\":"<<returned_<<",\\"overwritten\\":"<<s.overwritten<<",\\"rejected\\":"<<s.rejected<<",\\"reconnect_discarded\\":"<<s.reconnect_discarded<<",\\"final_after_join\\":true,\\"failure_path\\":"<<(failure?"true":"false")<<"}\\n";f.close();if(!f)throw std::runtime_error("Failure input summary write failed");saved_=true;}
TimedWindowInput::~TimedWindowInput(){if(!saved_)try{saveStats(true);}catch(...){} }
}
'''
put('software/pose_v1/src/stage_guard_window_input.cpp',source)
cm=(root/'tools/pose-v1/bounded-load-CMakeLists.txt').read_text(encoding='utf-8');cm=change(cm,'failure_source_readback.cpp mixed_host_check.cpp','failure_source_readback.cpp host_stage_observation.cpp mixed_host_check.cpp')
cm+='\nadd_executable(pose_stage_observation_selftest host_stage_observation_selftest.cpp host_stage_observation.cpp)\ntarget_include_directories(pose_stage_observation_selftest PRIVATE .)\ntarget_link_libraries(pose_stage_observation_selftest PRIVATE Threads::Threads)\ntarget_compile_options(pose_stage_observation_selftest PRIVATE -Wall -Wextra -Wpedantic)\n'
put('tools/pose-v1/stage-guard-CMakeLists.txt',cm)
builder=(root/'tools/pose-v1/Build-BoundedLoadR2.ps1').read_text(encoding='utf-8').replace('mixed-20261009-bounded-load-r2','mixed-20261009-stage-guard-r1')
builder=change(builder,"'pose_bounded_load_selftest','--parallel'","'pose_bounded_load_selftest','pose_stage_observation_selftest','--parallel'")
builder=change(builder,'$poseHashes = [ordered]@{}',"Invoke-MixedDocker @('cp',($poseContainer+':'+$poseRemote+'/build/pose_stage_observation_selftest'),(Join-Path $poseOutput 'pose_stage_observation_selftest'))\n$poseHashes = [ordered]@{}")
builder=change(builder,"stage='compiled_not_executed'; container='FPAI';","stage='compiled_not_executed'; container='FPAI';\n    stage_selftest_sha256=(Get-FileHash -LiteralPath (Join-Path $poseOutput 'pose_stage_observation_selftest') -Algorithm SHA256).Hash.ToLowerInvariant();")
put('tools/pose-v1/Build-StageGuard.ps1',builder)
runner=(root/'tools/pose-v1/run-bounded-load.sh').read_text(encoding='utf-8');needle='if test "$au_code" = 0; then\nif test "$stage" = host-check; then'
runner=change(runner,needle,'''if test "$au_code" = 0 && test "$stage" = host-check; then
    cp "$work/pose_stage_observation_selftest" "$run/pose_stage_observation_selftest"
    timeout --signal=TERM --kill-after=2s 10s "$work/pose_stage_observation_selftest" "$run/stage-contracts" > "$run/stage-contracts.stdout.log" 2> "$run/stage-contracts.stderr.log"
    au_code=$?
    printf '%s\\n' "$au_code" > "$run/stage-contracts.exit.txt"
fi
'''+needle)
put('tools/pose-v1/run-stage-guard.sh',runner)
review=(root/'tools/pose-v1/review_bounded_load_r2_stage.py').read_text(encoding='utf-8').replace('Build-BoundedLoadR2.ps1','Build-StageGuard.ps1').replace('run-bounded-load.sh','run-stage-guard.sh');review=change(review,"'bounded_frozen_sources')","'bounded_frozen_sources','stage_guard_frozen_sources')")
put('tools/pose-v1/review_stage_guard.py',review)
mapping={'software/pose_v1/src/bounded_load_check_r1.cpp':'software/pose_v1/src/stage_guard_check_r1.cpp','software/pose_v1/src/source_application_bridge_r4.cpp':'software/pose_v1/src/stage_guard_bridge_r1.cpp','software/pose_v1/src/source_failure_adapter_test_r4.cpp':'software/pose_v1/src/stage_guard_host_probe_r1.cpp','software/pose_v1/include/tcp_receiver.hpp':'software/pose_v1/include/stage_guard_tcp_receiver.hpp','software/pose_v1/src/tcp_receiver.cpp':'software/pose_v1/src/stage_guard_tcp_receiver.cpp','software/pose_v1/include/process_window_input.hpp':'software/pose_v1/include/stage_guard_window_input.hpp','software/pose_v1/src/process_window_input.cpp':'software/pose_v1/src/stage_guard_window_input.cpp','tools/pose-v1/bounded-load-CMakeLists.txt':'tools/pose-v1/stage-guard-CMakeLists.txt'}
m['stage_guard_frozen_sources']={rel:g.sha(root/rel) for rel in mapping}
for before,after in mapping.items():item=m['build_files'].pop(before);m['build_files'][after]=dict(destination=item['destination'],sha256=g.sha(root/after))
for rel in ['include/host_stage_observation.hpp','src/host_stage_observation.cpp','src/host_stage_observation_selftest.cpp']:
    full='software/pose_v1/'+rel;m['build_files'][full]=dict(destination=Path(rel).name,sha256=g.sha(root/full))
for name in ['prepare_stage_guard_r1.py','Build-StageGuard.ps1','run-stage-guard.sh','review_stage_guard.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-StageGuard.ps1';m['stage_guard']=dict(explicit_sync_op=582,fused_group=9189,target_layer_count=638,maximum_layer_count=745,source_producers=[8130,8131],no_582_ancestor_in_group=True,snapshot_after_original_copy=True,snapshot_limit_per_call=1048576,alignment_checks='FP324-byte/byte bounds/non-overlap;64/128/256 modulo metadata only',DMA_cache_fence_proven=False,zero_copy=False)
out=root/'.local/pose-v1-stage-guard/package-20261009-r1';assert not out.exists();shutil.copytree(base,out);(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
