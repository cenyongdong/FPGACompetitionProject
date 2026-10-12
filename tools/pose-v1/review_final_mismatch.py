"""Final-gate diagnosis: compare owned Host/CPU/late public reads; never accept a failed run."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();g.verify(a.run)
o=a.run/'results';rows=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
calls=rows(o/'inference.jsonl');clock=rows(o/'timing.jsonl');assert len(calls)==len(clock)<=103
index=g.load(o/'owned-result-index.json');assert index['count']==len(calls) and not index['serializer_compared_math']
def compare(actual,baseline):
    assert len(actual)==len(baseline) and len(actual)%4==0
    aa=np.frombuffer(actual,'<f4');bb=np.frombuffer(baseline,'<f4');changed=np.flatnonzero(aa.view('<u4')!=bb.view('<u4'));finite=np.isfinite(aa)&np.isfinite(bb)
    return dict(changed_FP32=len(changed),nonfinite_actual=int((~np.isfinite(aa)).sum()),finite_max_abs=float(np.abs(aa[finite].astype(float)-bb[finite].astype(float)).max()) if finite.any() else None,changed_first64=changed[:64].tolist(),bitwise_equal=actual==baseline)
returned=[]
for i,c in enumerate(calls):
    assert c['call']==c['invocation']==i and c['frame_id']==clock[i]['transport_id']
    tensors={}
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:
        blob=(o/f'result{i}.{suffix}.f32').read_bytes();assert blob==(o/f'presaved-results/{i}/{suffix}.f32').read_bytes();tensors[suffix]=compare(blob,(a.package/folder/f"{c['case']}.{suffix}.f32").read_bytes())
    assert (o/f'result{i}.raw-payload.bin').read_bytes()==(o/f'presaved-results/{i}/raw-payload.bin').read_bytes()==(a.package/'inputs'/f"{c['case']}.csi").read_bytes()[32:]
    returned.append(dict(invocation=i,case=c['case'],runtime_gate_completed=c['runtime_gate_completed'],tensors=tensors))
bad=[x for x in returned if not x['runtime_gate_completed']];assert len(bad)==1 and bad[0]['invocation']==len(calls)-1
assert all(all(v['bitwise_equal'] for v in x['tensors'].values()) for x in returned[:-1])
idx=g.load(o/'final-output-source-readback/index.json');assert idx['invocation']==bad[0]['invocation'] and idx['frame']==calls[-1]['frame_id'] and idx['no_forward_or_reset'] and idx['physical_reuse_possible']
gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1';g.verify(gold);catalog=rows(gold/'results/content/index.jsonl');case=calls[-1]['case'];root=o/'final-output-source-readback';sources=[];outputs=[]
def reference(kind,op,slot):
    candidates=[x for x in catalog if x['case']==case and x['kind']==kind and x['op_id']==op and x['slot']==slot];assert candidates
    blobs=[(gold/'results/content'/x['file']).read_bytes() for x in candidates];assert all(x==blobs[0] for x in blobs)
    for x in candidates:
        for suffix in ['scores','poses']:assert (gold/f"results/call{x['invocation']}.{suffix}.f32").read_bytes()==(a.package/'r6-reference'/f'{case}.{suffix}.f32').read_bytes()
    return blobs[0]
for s in idx['sources']:
    op,slot=s['op'],s['slot'];baseline=reference('bridge_input',op,slot);host=(root/f'host.{op}.{slot}.f32').read_bytes();assert len(host)==s['bytes']==16800
    record=dict(op=op,slot=slot,storage=s['storage'],Host_vs_gold=compare(host,baseline),late=[])
    for round in range(2):
        item=next(x for x in idx['reads'] if x['round']==round and x['op']==op and x['slot']==slot)
        if item['complete']:
            blob=(root/f'round{round}.{op}.{slot}.f32').read_bytes();record['late'].append(dict(round=round,begin_ns=item['begin_ns'],end_ns=item['end_ns'],vs_Host=compare(blob,host),vs_gold=compare(blob,baseline)))
        else:record['late'].append(dict(round=round,complete=False,error=item['error']))
    sources.append(record)
for s in idx['cpu_outputs']:
    op,slot=s['op'],s['slot'];blob=(root/f'cpu.{op}.{slot}.f32').read_bytes();assert len(blob)==s['bytes'];outputs.append(dict(op=op,slot=slot,vs_gold=compare(blob,reference('bridge_result',op,slot))))
ledger=g.load(o/'persistence-ledger.json');assert len(ledger['tasks'])==8 and ledger['original_computation_failure'] and all(x['saved'] for x in ledger['tasks'])
assert (a.run/'exit.txt').read_text().strip()=='1' and (a.run/'dmesg.before.log').read_bytes()==(a.run/'dmesg.after.log').read_bytes()
life=rows(o/'lifecycle.jsonl');assert [x['event'] for x in life]==['Engine_created','workers_joined','Engine_destroyed']
for line in (a.run/'final.processes').read_text().splitlines()[1:]:assert len(line.split())<2 or not line.split()[1].startswith('pose_')
assert not any(x in (a.run/'final.ports').read_text() for x in [':39001 ',':8554 '])
report=dict(status='final_output_failure_full_owned_and_late_evidence_compared_not_acceptance',complete_correct=len(calls)-1,owned_returned=len(calls),failure=bad[0],returned=returned,source_comparison=sources,CPU_output_comparison=outputs,read_capture_error=idx['capture_error'],all_eight_persistence_tasks_saved=True,kernel_unchanged=True,Engine_destroyed_after_join=True,all_services_closed=True,late_physical_reuse_possible=True,root_cause_proven=False)
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Full failure evidence compared:',len(calls),'returns; capture error:',idx['capture_error'])
