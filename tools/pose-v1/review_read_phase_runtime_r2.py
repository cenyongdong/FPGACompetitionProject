"""Owned snapshot contracts and actual first-read/pre-CPU bytes; local only."""
import argparse,json
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
p=argparse.ArgumentParser();p.add_argument('kind',choices=['core','SDK','runtime']);p.add_argument('--root',type=Path,required=True);p.add_argument('--package',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
rows=[json.loads(x) for x in (a.root/'metadata.jsonl').read_text().splitlines()];s=g.load(a.root/'summary.json');assert len(rows)==s['rows'] and s['per_frame_bytes']==33600 and s['no_second_read'] and s['no_repair']
def fnv(b):
    h=14695981039346656037
    for c in b:h=((h^c)*1099511628211)&((1<<64)-1)
    return h
def diff(b,c):
    assert len(b)==len(c)==16800;v=np.frombuffer(b,'<f4');w=np.frombuffer(c,'<f4')
    return dict(changed_FP32=int((v.view('<u4')!=w.view('<u4')).sum()),nonfinite=int((~np.isfinite(v)).sum()),noninteger=int((np.isfinite(v)&(v!=np.trunc(v))).sum()),bitwise=b==c)
results=[]
for i,row in enumerate(rows):
    assert row['invocation']==i
    if row['read_done']:assert row['read_begin_ns']<=row['read_return_ns']
    if row['cpu_snapshot_done']:assert row['read_done'] and row['read_return_ns']<=row['before_CPU_ns']
    d=a.root/f'frame{i}'
    if d.exists():
        files={key:(d/name).read_bytes() for key,name in [('immediate','immediate.f32'),('cpu','before-CPU.f32')] if (d/name).exists()}
        if row['read_done']:assert fnv(files['immediate'])==row['immediate_FNV64_diagnostic_only']
        if row['cpu_snapshot_done']:
            assert fnv(files['cpu'])==row['CPU_FNV64_diagnostic_only']
            assert sum(x!=y for x,y in zip(files['immediate'],files['cpu']))==row['byte_changes']
        record=dict(invocation=i,frame=row['frame'],immediate_to_CPU_byte_changes=row['byte_changes'])
        if a.kind=='core':
            if i==0:assert files['immediate']==bytes(16800) and files['cpu'][9]==42 and sum(files['cpu'])==42
            elif i==102:assert not files and row['error']=='Injected\nread\x1b failure'
            else:assert files['immediate']==files['cpu']==bytes(16800)
        elif a.kind=='SDK':
            wanted=(np.arange(4200)%180).astype('<f4').tobytes();assert files['immediate']==files['cpu']==wanted
        else:
            assert a.package
            catalog=[x.split()[1] for x in (a.package/'cases.tsv').read_text().splitlines() if x.split()[0]=='expanded']
            # Runtime invocations can overwrite inputs; actual transport ID defines source.
            completed=[json.loads(x) for x in (a.root.parent/'inference.jsonl').read_text().splitlines()]
            found=[x for x in completed if x['invocation']==i];assert len(found)<=1
            if found:
                assert found[0]['frame_id']==row['frame'];case=found[0]['case']
            elif row['frame']>=100000:case=catalog[(row['frame']-100000)%27]
            else:raise AssertionError('Unknown runtime transport identity')
            baseline_values=[]
            for run in [g.ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-three',g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1']:
                g.verify(run);gold=run/'results/content';index=[json.loads(x) for x in (gold/'index.jsonl').read_text().splitlines()]
                matches=[x for x in index if x['case']==case and x['op_id']==192 and x['slot']==1 and x['kind']=='bridge_input']
                baseline_values.extend((gold/x['file']).read_bytes() for x in matches)
            assert baseline_values;baseline=baseline_values[0];assert all(b==baseline for b in baseline_values)
            record.update(case=case,immediate_vs_gold=diff(files['immediate'],baseline),CPU_vs_gold=diff(files['cpu'],baseline))
        results.append(record)
if a.kind=='core':assert len(rows)==103 and [x['invocation'] for x in results]==[0,1,2,3,102]
if a.kind=='SDK':assert len(rows)==1 and rows[0]['byte_changes']==0
a.output.write_text(json.dumps(dict(status='owned_read_phase_reviewed',kind=a.kind,rows=len(rows),owned_frames=len(results),results=results,root_cause_proven=False),indent=2)+'\n',encoding='utf-8',newline='\n');print('Read-phase snapshots verified:',a.kind,len(rows),len(results))
