"""Failure chronology, complete returned values and original/late bytes; local only."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();g.verify(a.run)
o=a.run/'results';b=g.load(a.build/'build-result.json');assert g.sha(a.run/'pose_read_phase_check')==b['phase_binary_sha256'];assert g.sha(a.package/'manifest.json')==b['package_manifest_sha256']
rows=lambda f:[json.loads(x) for x in f.read_text().splitlines()]
calls=rows(o/'inference.jsonl');timing=rows(o/'timing.jsonl');assert len(calls)==len(timing)==48
for i,c in enumerate(calls):
    assert c['call']==c['invocation']==i and c['frame_id']==timing[i]['transport_id']==100000+timing[i]['sequence'] and c['runtime_gate_completed'] and c['before_forward']==0 and c['completed_layers']==745
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:assert (o/f'result{i}.{suffix}.f32').read_bytes()==(o/f'presaved-results/{i}/{suffix}.f32').read_bytes()==(a.package/folder/f"{c['case']}.{suffix}.f32").read_bytes()
failure=g.load(o/'failed-host-inputs/failure.json');assert failure['invocation']==48 and failure['frame_id']==100049 and failure['op_id']==192
phase=rows(o/'read-phase/metadata.jsonl');assert len(phase)==49 and all(x['read_done'] and x['cpu_snapshot_done'] and x['byte_changes']==0 for x in phase)
current=phase[-1];assert current['error']==failure['error'];assert current['before_identity']==current['after_identity'] and current['CPU_identity']==current['before_identity']['destination']
immediate=(o/'read-phase/frame48/immediate.f32').read_bytes();cpu=(o/'read-phase/frame48/before-CPU.f32').read_bytes();assert immediate==cpu==(o/'failed-host-inputs/input1.f32').read_bytes()==(o/'failed-invocation-inputs/op192.slot1.f32').read_bytes()
gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1';g.verify(gold);index=rows(gold/'results/content/index.jsonl');case='S52_18_317'
def baseline(op,slot):
    refs=[x for x in index if x['case']==case and x['kind']=='bridge_input' and x['op_id']==op and x['slot']==slot];assert refs
    values=[(gold/'results/content'/x['file']).read_bytes() for x in refs];assert all(v==values[0] for v in values);return values[0]
def compare(x,y):
    assert len(x)==len(y);v=np.frombuffer(x,'<f4');w=np.frombuffer(y,'<f4');diff=np.flatnonzero(v.view('<u4')!=w.view('<u4'))
    return dict(changed_FP32=len(diff),nonfinite=int((~np.isfinite(v)).sum()),noninteger=int((np.isfinite(v)&(v!=np.trunc(v))).sum()),bitwise=x==y,changed_indices=diff.tolist())
wanted=baseline(192,1);bad=compare(immediate,wanted);assert bad['changed_FP32']==592 and bad['noninteger']==589 and bad['nonfinite']==0
assert (o/'failed-invocation-inputs/op188.slot0.f32').read_bytes()==baseline(188,0)
data=(o/'failed-host-inputs/input0.f32').read_bytes();assert data==baseline(192,0)==(o/'failed-invocation-inputs/op192.slot0.f32').read_bytes()
read=g.load(o/'failed-host-inputs/source-readback/readback.json');assert read['status']=='two_SDK_source_reads_completed' and read['single_round_bytes']==47040
late=[]
for round in range(2):
    assert (o/f'failed-host-inputs/source-readback/round{round}.input0.f32').read_bytes()==data
    value=(o/f'failed-host-inputs/source-readback/round{round}.input1.f32').read_bytes();assert value==wanted;late.append(compare(value,wanted))
changed=np.asarray(bad['changed_indices']);original=np.frombuffer(immediate,'<u4');slot0=np.frombuffer(data,'<u4');matching=int((original[changed]==slot0[changed]).sum())
for name,size in [('persistence-ledger',8),('upstream-persistence-ledger',1),('read-phase-persistence-ledger',1)]:
    l=g.load(o/(name+'.json'));assert len(l['tasks'])==size and all(t['saved'] for t in l['tasks']) and l['original_computation_failure']
assert (a.run/'exit.txt').read_text().strip()=='1' and (a.run/'dmesg.before.log').read_bytes()==(a.run/'dmesg.after.log').read_bytes()
assert [x['event'] for x in rows(o/'lifecycle.jsonl')]==['Engine_created','workers_joined','Engine_destroyed']
assert not any(line.split()[1].startswith('pose_') for line in (a.run/'final.processes').read_text().splitlines()[1:] if len(line.split())>1)
assert not any(port in (a.run/'final.ports').read_text() for port in [':39001 ',':8554 '])
report=dict(status='read_return_snapshot_already_bad_CPU_boundary_unchanged_failure_preserved',binary_sha256=b['phase_binary_sha256'],manifest_sha256=b['package_manifest_sha256'],complete_correct=48,correct_FP32=724800,failed_invocation=48,frame=100049,case=case,op=192,first_snapshot_vs_gold=bad,first_equals_beforeCPU_and_original_failure_Host=True,all49_immediate_to_CPU_byte_changes=0,two_late_source_reads_bitwise_gold=True,late_bytes=94080,changed_values_equal_same_offset_previous_slot0=matching,changed_values_total=len(changed),read_duration_ns=current['read_return_ns']-current['read_begin_ns'],read_return_to_CPU_snapshot_ns=current['before_CPU_ns']-current['read_return_ns'],read_return_to_first_late_index_read_ns=read['sources'][1]['reads'][0]['begin_ns']-current['read_return_ns'],Host_destination_mod64=current['CPU_identity']['address']%64,identity_stable=True,original8_upstream1_phase1_saved=True,kernel_unchanged=True,cleanup_verified=True,current_not_reached_Gather442=True,root_cause_proven=False)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Failure chronology verified: first snapshot already bad, CPU unchanged, late correct; same-offset slot0 matches',matching,'of',len(changed))
