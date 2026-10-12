"""The observer was not linked: prove numeric returns without granting stage acceptance."""
import json
import mixed_validation_gate as g
r=g.ROOT;e=r/'tools/pose-v1/evidence/read-phase-20261011-r2';run=e/'process-three-return/run-process-three';o=run/'results';package=r/'.local/pose-v1-read-phase/package-20261011-r2';g.verify(run)
calls=[json.loads(x) for x in (o/'inference.jsonl').read_text().splitlines()];assert len(calls)==4
for i,c in enumerate(calls):
    assert c['invocation']==c['call']==i and c['runtime_gate_completed'] and c['completed_layers']==745
    for suffix,folder in [('input','reference'),('scores','r6-reference'),('poses','r6-reference')]:assert (o/f'result{i}.{suffix}.f32').read_bytes()==(o/f'presaved-results/{i}/{suffix}.f32').read_bytes()==(package/folder/f"{c['case']}.{suffix}.f32").read_bytes()
for name,n in [('persistence-ledger',8),('upstream-persistence-ledger',1)]:
    l=g.load(o/(name+'.json'));assert len(l['tasks'])==n and not l['original_computation_failure'] and all(t['saved'] for t in l['tasks'])
phase=g.load(o/'read-phase-persistence-ledger.json');assert not phase['original_computation_failure'] and len(phase['tasks'])==1 and not phase['tasks'][0]['saved'] and phase['tasks'][0]['error']=='Preserve read phase evidence'
assert not (o/'read-phase').exists() and (run/'exit.txt').read_text().strip()=='1'
life=[json.loads(x) for x in (o/'lifecycle.jsonl').read_text().splitlines()];assert [x['event'] for x in life]==['Engine_created','workers_joined','Engine_destroyed']
assert (run/'dmesg.before.log').read_bytes()==(run/'dmesg.after.log').read_bytes()
assert not any(line.split()[1].startswith('pose_') for line in (run/'final.processes').read_text().splitlines()[1:] if len(line.split())>1)
assert not any(port in (run/'final.ports').read_text() for port in [':39001 ',':8554 '])
f=e/'three-wiring-failure-review.json';assert not f.exists();f.write_text(json.dumps(dict(status='four_numeric_returns_correct_observer_unwired_not_acceptance',FP32=60400,original8_upstream1_saved=True,read_phase_empty_refused=True,exit=1,kernel_unchanged=True,cleaned_after_join=True,high_load_not_executed=True),indent=2)+'\n',encoding='utf-8',newline='\n');print('r2 failure retained: four correct returns, observer unwired, no high-load')
