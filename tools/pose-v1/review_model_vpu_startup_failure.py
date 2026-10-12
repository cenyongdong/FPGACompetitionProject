"""Review a pre-Engine VPU failure without weakening successful stage gates."""
import json,re
import mixed_validation_gate as g
from review_model_vpu_build_base import identities,rows

e=g.ROOT/'tools/pose-v1/evidence/model-vpu-20261010-r2'
r=e/'vpu-103-return/run-vpu-103';out=r/'results'
m,b,n=identities(g.ROOT/'.local/pose-v1-model-vpu/package-20261010-r2',g.ROOT/'.local/pose-v1-build/mixed-20261010-model-vpu-r2')
assert g.sha(e/'vpu-103.tar')=='123093cf8d6f95e9b426b0d4dda015106daea6647d7c52b7d783eb0391cc290c'
assert g.sha(r/'pose_model_vpu_check')==b['model_vpu_binary_sha256'] and (r/'exit.txt').read_text().strip()=='1'
assert g.sha(r/'executed-runner.sh')==g.sha(g.ROOT/'tools/pose-v1/run-model-vpu.sh')
count=g.verify(r);summary=g.load(out/'summary.json');v=g.load(out/'vpu/summary.json')
assert summary['mode']=='load-103' and summary['expected']==103 and summary['attempted']==summary['returned']==summary['correct']==0
assert not summary['passed'] and not summary['Engine_stopped_after_error'] and summary['load_joined'] and summary['VPU']
assert v['joined'] and not v['drained'] and v['first_capture_ns']==v['last_capture_ns']==v['packets']==v['submitted']==v['returned']==0
life=rows(out/'lifecycle.jsonl');assert [x['event'] for x in life]==['load_joined','Engine_destroyed']
assert not any((out/name).read_bytes() for name in ['inference.jsonl','returned-index.jsonl','timing.jsonl'])
ledger=g.load(out/'persistence-ledger.json');assert ledger['original_computation_failure'] and len(ledger['tasks'])==7 and all(x['saved'] for x in ledger['tasks'])
assert (r/'stderr.log').read_text().strip()=='STOP: DQBUF: Input/output error'
assert not (out/'vpu/encoder/video.h264').read_bytes() and not (out/'failed-host-inputs').exists()
before=(r/'dmesg.before.log').read_bytes();after=(r/'dmesg.after.log').read_bytes();assert after.startswith(before)
added=after[len(before):].decode();assert 'page allocation failure: order:7' in added and 'GFP_KERNEL|__GFP_NORETRY|__GFP_ZERO' in added and 'mvx_mmu_alloc_contiguous_pages' in added and 'map_protocol_v2' in added and '0*512kB' in added
events=rows(out/'vpu/encoder/events.jsonl');errors=[x for x in events if x['event']=='dqbuf_error'];assert len(errors)==1 and errors[0]['type']==9 and errors[0]['errno']==5
aborts=[x for x in events if x['event']=='abort_streamoff'];assert len(aborts)==2 and {x['type'] for x in aborts}=={9,10} and all(x['result']==0 for x in aborts)
queued=[x for x in events if x['event']=='input_queued'];assert len(queued)==2 and not any(x['event']=='capture' for x in events)
assert not any(line.split(maxsplit=2)[1].startswith('pose_') for line in (r/'final.processes').read_text().splitlines()[1:])
assert all(port not in (r/'final.ports').read_text() for port in (':39001 ',':8554 '))

def units(text):
    total=0
    for line in text.splitlines():
        match=re.search(r'type\s+(Unmovable|Movable|Reclaimable|HighAtomic)\s+([\d\s]+)$',line)
        if match:
            values=list(map(int,match[2].split()));assert len(values)==11;total+=sum(values[i]*2**(i-7) for i in range(7,11))
    return total
snapshots=[]
for x in events:
    if x['event']=='memory_snapshot':
        p=out/'vpu/encoder/memory';prefix=x['prefix']
        snapshots.append(dict(stage=x['stage'],time_ns=x['time_ns'],ordinary_512KiB_units=units((p/(prefix+'-pagetypeinfo.txt')).read_text()),files_SHA256={n:g.sha(p/(prefix+'-'+n+'.txt')) for n in ('buddyinfo','pagetypeinfo','meminfo','vmstat')}))
report=dict(status='model_vpu_startup_failed_preserved_not_acceptance',stage='vpu-103',model_vpu_binary_sha256=b['model_vpu_binary_sha256'],package_manifest_sha256=b['package_manifest_sha256'],payloads=n,returned_files=count,expected_calls=103,attempted=0,correct=0,FP32_compared=0,Engine_created=False,Engine_destroyed_event_is_null_reset_cleanup=True,NPU_forward_executed=False,first_capture=False,synthetic_frames_encoded=0,raw_inputs_queued=2,original_exception='DQBUF: Input/output error',new_kernel_events=True,new_kernel_events_SHA256=__import__('hashlib').sha256(added.encode()).hexdigest(),failure_allocation_order=7,failure_allocation_bytes=524288,failure_allocation_flags='GFP_KERNEL|__GFP_NORETRY|__GFP_ZERO',allocation_path='mvx_mmu_alloc_contiguous_pages -> map_protocol_v2 -> mvx_fw_factory',worker_joined=True,both_abort_STREAMOFF_succeeded=True,persistence_tasks_saved=7,programs_remaining=0,ports_released=True,old_model_fault_reproduced=False,VPU_model_fault_cause_proven=False,resource_snapshots=snapshots,model_VPU103_acceptance=False)
p=e/'vpu-103.failed-review.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='resource_snapshots'}))
