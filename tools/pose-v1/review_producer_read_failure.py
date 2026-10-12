"""Analyze original saved failure and two owned late sources; no repair/rerun."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-source-read-20261011-r2';D=E/'on-return/run-on';P=D/'results';ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (D/'exit.txt').read_text().strip()=='1';summary=load(P/'summary.json');leases=load(P/'lease-summary.json');failure=(P/'failure.txt').read_text()
assert leases['opened']==leases['closed'] and leases['forced_expired']==0
assert load(P/'release.json')['remaining_sdk_chunks']==0 and load(P/'prefix-release.json')['after_prefix_drop_chunks']==0
assert not (P/'lease-release.error.txt').exists() and not (P/'prefix-release.error.txt').exists()
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
values=0
for i in range(summary['completed']):
    d=P/('call-'+str(i));pattern=ref/('pattern-'+str(i%2));t=load(d/'trace.json');assert t['before_forward_count']==0 and t['after_ready_count']==11
    for n in ('input-486.f32','input-478.f16','output-4386.f32','output-4390.f32'):
        assert (d/n).read_bytes()==(pattern/n).read_bytes()
        if n.startswith('output'):a=np.fromfile(d/n,dtype='<f4');assert np.isfinite(a).all();values+=a.size
bad_i=summary['completed'];d=P/('call-'+str(bad_i));assert not (P/('call-'+str(bad_i+1))).exists();t=load(d/'trace.json');pattern=ref/('pattern-'+str(bad_i%2));details={}
for n in ('input-486.f32','input-478.f16'):assert (d/n).read_bytes()==(pattern/n).read_bytes()
for v in (4386,4390):
    name='output-'+str(v)+'.f32';a=np.fromfile(d/name,dtype='<u4');b=np.fromfile(pattern/name,dtype='<u4');bad=np.flatnonzero(a!=b);groups=np.split(bad,np.flatnonzero(np.diff(bad)>1)+1) if bad.size else []
    previous=np.fromfile(P/('call-'+str(bad_i-1))/name,dtype='<u4') if bad_i else None
    details[str(v)]={'changed_count':int(bad.size),'nonfinite_count':int((~np.isfinite(a.view('<f4'))).sum()),'same_previous_offset':int((a[bad]==previous[bad]).sum()) if previous is not None else None,
                     'first_sha256':sha(d/name),'expected_sha256':sha(pattern/name),'runs':[[int(g[0]*4),int((g[-1]+1)*4)] for g in groups]}
late=d/'late-source';reads=[json.loads(x) for x in (late/'reads.jsonl').read_text().splitlines()];assert len(reads)==4
assert leases['failure_capture_calls']==1 and leases['source_read_calls']==4 and not (d/'source-read.error.txt').exists()
assert load(late/'summary.json')['bytes']==94080
for entry in reads:
    v=entry['value'];index=0 if v==4386 else 1;source=t['reads'][index];name='round-'+str(entry['round'])+'-'+str(v)+'.f32'
    for field in ('source_address','source_offset','source_capacity'):assert entry[field]==source[field]
    assert entry['chunk_identity']==source['source_chunk_identity'] and entry['invocation']==bad_i
    assert entry['metadata_ns']<=entry['read_begin_ns']<=entry['read_end_ns']<=entry['saved_ns']
    a=np.fromfile(late/name,dtype='<u4');b=np.fromfile(pattern/('output-'+str(v)+'.f32'),dtype='<u4');first=np.fromfile(d/('output-'+str(v)+'.f32'),dtype='<u4')
    entry['changed_vs_expected']=int((a!=b).sum());entry['changed_vs_first']=int((a!=first).sum());entry['nonfinite']=int((~np.isfinite(a.view('<f4'))).sum());entry['sha256']=sha(late/name)
assert all(a['saved_ns']<=b['metadata_ns'] for a,b in zip(reads,reads[1:]))
events=[json.loads(x) for x in (P/'phases.jsonl').read_text().splitlines()];forward=sum(x['phase']=='forward' and x['edge']=='begin' for x in events)
assert forward==leases['opened'] and forward==bad_i+1 and t['before_forward_count']==0 and t['after_ready_count']==11
r={'status':'original_failure_and_owned_late_sources_verified','failure':failure,'completed_correct':bad_i,'forward_calls':forward,'FP32_correct_prefix':values,'failed_invocation':bad_i,
   'first_outputs':details,'late_sources':reads,'late_bytes':94080,'first_outputs_hashes_after_review':{str(v):sha(d/('output-'+str(v)+'.f32')) for v in (4386,4390)},
   'first_saved_files_not_repaired':True,'source_read_calls':4,'counter_not_fence':True,'lease_summary':leases,'kernel_unchanged':True,
   'API':'public Tensor::read to owned bytes; no added wait/reset/forward/write/sleep','normal_drain_LAST_pass':False,'root_cause_resolved':False,'no_hardware_retry':True}
(E/'on.failure-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('Preserved failure',bad_i,'first changed',[details[str(v)]['changed_count'] for v in (4386,4390)],'late changed',[x['changed_vs_expected'] for x in reads])
