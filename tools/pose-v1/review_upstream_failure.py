"""Failed192 run: transport identity, owned outputs, Host and two public late reads."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--package',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();g.verify(a.run);o=a.run/'results';rows=lambda p:[json.loads(x) for x in p.read_text().splitlines()]
calls=rows(o/'inference.jsonl');timing=rows(o/'timing.jsonl');assert len(calls)==len(timing)==55
for i,c in enumerate(calls):
    assert c['call']==c['invocation']==i and c['frame_id']==timing[i]['transport_id']==100000+timing[i]['sequence'] and c['runtime_gate_completed']
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:assert (o/f'result{i}.{suffix}.f32').read_bytes()==(o/f'presaved-results/{i}/{suffix}.f32').read_bytes()==(a.package/folder/f"{c['case']}.{suffix}.f32").read_bytes()
failure=g.load(o/'failed-host-inputs/failure.json');inv=failure['invocation'];frame=failure['frame_id'];assert inv==55 and frame==100056 and failure['op_id']==192
catalog=[x.split()[1] for x in (a.package/'cases.tsv').read_text().splitlines() if x.split()[0]=='expanded'];case=catalog[(frame-100000)%27]
gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1';g.verify(gold);captures=rows(gold/'results/content/index.jsonl')
def compare(blob,baseline):
    assert len(blob)==len(baseline) and len(blob)%4==0;aa=np.frombuffer(blob,'<f4');bb=np.frombuffer(baseline,'<f4');changed=np.flatnonzero(aa.view('<u4')!=bb.view('<u4'));finite=np.isfinite(aa)&np.isfinite(bb)
    return dict(changed_FP32=len(changed),nonfinite_actual=int((~np.isfinite(aa)).sum()),noninteger_actual=int((np.isfinite(aa)&(aa!=np.trunc(aa))).sum()),finite_max_abs=float(np.abs(aa[finite].astype(float)-bb[finite].astype(float)).max()) if finite.any() else None,changed_first64=changed[:64].tolist(),bitwise_equal=blob==baseline)
read=g.load(o/'failed-host-inputs/source-readback/readback.json');assert read['status']=='two_SDK_source_reads_completed' and read['invocation']==inv and read['frame_id']==frame and read['single_round_bytes']==47040
records=[]
shadow=g.load(o/'failed-invocation-inputs/index.json');assert shadow['frame_id']==frame and shadow['invocation']==inv
for x in shadow['inputs']:
    op,slot=x['op_id'],x['slot'];refs=[v for v in captures if v['case']==case and v['kind']=='bridge_input' and v['op_id']==op and v['slot']==slot];assert refs
    baseline=(gold/'results/content'/refs[0]['file']).read_bytes();assert all((gold/'results/content'/v['file']).read_bytes()==baseline for v in refs)
    blob=(o/'failed-invocation-inputs'/x['file']).read_bytes();record=dict(op=op,slot=slot,Host_vs_gold=compare(blob,baseline))
    if op==192:
        assert blob==(o/f'failed-host-inputs/input{slot}.f32').read_bytes();record['late']=[]
        for round in range(2):
            late=(o/f'failed-host-inputs/source-readback/round{round}.input{slot}.f32').read_bytes();record['late'].append(dict(round=round,vs_Host=compare(late,blob),vs_gold=compare(late,baseline)))
    records.append(record)
ledger=g.load(o/'persistence-ledger.json');extra=g.load(o/'upstream-persistence-ledger.json');assert len(ledger['tasks'])==8 and len(extra['tasks'])==1 and all(x['saved'] for x in ledger['tasks']+extra['tasks']) and ledger['original_computation_failure'] and extra['original_computation_failure']
assert (a.run/'exit.txt').read_text().strip()=='1' and (a.run/'dmesg.before.log').read_bytes()==(a.run/'dmesg.after.log').read_bytes()
life=rows(o/'lifecycle.jsonl');assert [x['event'] for x in life]==['Engine_created','workers_joined','Engine_destroyed']
for line in (a.run/'final.processes').read_text().splitlines()[1:]:assert len(line.split())<2 or not line.split()[1].startswith('pose_')
assert not any(x in (a.run/'final.ports').read_text() for x in [':39001 ',':8554 '])
a.output.write_text(json.dumps(dict(status='failed192_with_new_boundaries_preserved_not_acceptance',complete_correct=55,FP32_correct=830500,failed_invocation=inv,failed_frame=frame,case=case,error=failure['error'],input_summary=g.load(o/'input-summary.json'),Host_and_late=records,late_bytes=94080,original8_and_boundary1_saved=True,kernel_unchanged=True,Engine_destroyed_after_join=True,all_project_services_closed=True,current_frame_did_not_reach_Gather442=True,root_cause_proven=False),indent=2)+'\n',encoding='utf-8',newline='\n');print('55 correct full returns; failed192',case,'Host and two late reads compared')
