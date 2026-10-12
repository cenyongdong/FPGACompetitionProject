"""Review preparation timeout with no forward/read; preserve original deadline failure."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2';D=E/'on-return/run-on';P=D/'results';ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
load=lambda p:json.loads(p.read_text())
assert (D/'exit.txt').read_text().strip()=='1' and (P/'failure.txt').read_text()=='Prepared call missed absolute slot; no forward'
assert load(P/'summary.json')['completed']==49
lease=load(P/'lease-summary.json');assert lease['opened']==lease['closed']==49 and lease['forced_expired']==lease['source_read_calls']==lease['failure_capture_calls']==0
assert load(P/'release.json')['remaining_sdk_chunks']==0 and load(P/'prefix-release.json')['after_prefix_drop_chunks']==0
assert not (P/'lease-release.error.txt').exists() and not (P/'prefix-release.error.txt').exists()
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
values=0
for i in range(49):
    d=P/('call-'+str(i));pattern=ref/('pattern-'+str(i%2));t=load(d/'trace.json');assert t['before_forward_count']==0 and t['after_ready_count']==11
    for n in ('input-486.f32','input-478.f16','output-4386.f32','output-4390.f32'):
        assert (d/n).read_bytes()==(pattern/n).read_bytes()
        if n.startswith('output'):a=np.fromfile(d/n,dtype='<f4');assert np.isfinite(a).all();values+=a.size
assert values==576240 and not (P/'call-50').exists()
d=P/'call-49'
for n in ('input-486.f32','input-478.f16'):assert (d/n).read_bytes()==(ref/'pattern-1'/n).read_bytes()
assert not (d/'output-4386.f32').exists() and not (d/'output-4390.f32').exists() and not (d/'trace.json').exists() and not (d/'late-source').exists()
events=[json.loads(x) for x in (P/'phases.jsonl').read_text().splitlines()];assert len(events)==4842 and all(not x['trace_failed'] for x in events)
assert sum(x['phase']=='forward' and x['edge']=='begin' for x in events)==49
rows=load(E/'on.phase-spans.json')['spans'];last=[x for x in rows if x['inv']==49];directory=next(x for x in last if x['phase']=='directory');deadline=next(x for x in last if x['phase']=='deadline')
assert directory['ms']==915.85662 and directory['CPUms']==0.29944 and directory['voluntary']==2 and directory['majfault']==0
identity=load(d/'identity.json');assert deadline['begin_ns']>=identity['planned_ns']+198019801 and deadline['exceptional']
before=dict(x.split() for x in (D/'before.vmstat').read_text().splitlines());after=dict(x.split() for x in (D/'after.vmstat').read_text().splitlines());delta={k:int(after[k])-int(before[k]) for k in before if any(s in k for s in ('allocstall','pgscan','pgsteal','oom_kill','compact','pgmajfault'))}
r={'status':'directory_wait_preparation_deadline_failure_no_forward','completed_correct':49,'forward_calls':49,'FP32_correct_prefix':values,'failed_planned_invocation':49,
   'failure':(P/'failure.txt').read_text(),'directory_span':directory,'deadline_span':deadline,'failed_slot_inputs_saved':True,'failed_slot_outputs_exist':False,
   'lease_summary':lease,'failure_capture_triggered':False,'late_source_read_calls':0,'physical_late_source_capture_verified':False,
   'directory_wait_limit':'Wall time in filesystem::create_directory includes scheduler/filesystem/storage waiting; internal responsibility not proven.',
   'vmstat_delta':delta,'normal_drain_LAST_pass':False,'root_cause_resolved':False,'kernel_unchanged':True,'no_hardware_retry':True}
(E/'on.failure-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('49 correct/576240 FP32; slot49 directory915.85662ms wait; no reset/forward/output or source reads; deadline guard worked')
