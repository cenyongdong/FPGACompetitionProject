"""Analyze saved high-address failure without rereading hardware or repairing bytes."""
from pathlib import Path
import hashlib,json,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-address-20261011-r2';D=E/'on-return/run-on';P=D/'results';ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
load=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert (D/'exit.txt').read_text().strip()=='1' and (P/'failure.txt').read_text()=='Saved physical outputs differ from independent reference'
assert load(P/'summary.json')['completed']==49 and not load(P/'summary.json')['all_bitwise']
assert load(P/'release.json')['remaining_sdk_chunks']==0 and load(P/'prefix-release.json')['after_prefix_drop_chunks']==0 and not (P/'prefix-release.error.txt').exists()
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
values=0
for i in range(49):
    d=P/('call-'+str(i));pattern=ref/('pattern-'+str(i%2));trace=load(d/'trace.json')
    assert trace['before_forward_count']==0 and trace['after_ready_count']==11 and load(d/'comparison.json')['saved_before_compare']
    for name in ('input-486.f32','input-478.f16','output-4386.f32','output-4390.f32'):
        assert (d/name).read_bytes()==(pattern/name).read_bytes()
        if name.startswith('output'):a=np.fromfile(d/name,dtype='<f4');assert np.isfinite(a).all();values+=a.size
assert values==576240 and not (P/'call-50').exists()
d=P/'call-49';pattern=ref/'pattern-1';trace=load(d/'trace.json')
assert trace['before_forward_count']==0 and trace['after_ready_count']==11
for name in ('input-486.f32','input-478.f16'):assert (d/name).read_bytes()==(pattern/name).read_bytes()
bad_details={}
for value in (4386,4390):
    name='output-'+str(value)+'.f32';actual=np.fromfile(d/name,dtype='<u4');expected=np.fromfile(pattern/name,dtype='<u4');previous=np.fromfile(P/'call-48'/name,dtype='<u4')
    bad=np.flatnonzero(actual!=expected);groups=np.split(bad,np.flatnonzero(np.diff(bad)>1)+1) if bad.size else []
    floats=actual.view('<f4');runs=[{'start_element':int(g[0]),'end_exclusive_element':int(g[-1]+1),'start_byte':int(g[0]*4),'bytes':int(len(g)*4),'physical_start':trace['reads'][0 if value==4386 else 1]['source_address']+int(g[0]*4)} for g in groups]
    bad_details[str(value)]={'FP32_values':actual.size,'changed_count':int(bad.size),'nonfinite_count':int((~np.isfinite(floats)).sum()),'matches_previous_same_offset':int((actual[bad]==previous[bad]).sum()),'all_reference_differs_from_previous':int((expected!=previous).sum()),'runs':runs,'actual_sha256':sha(d/name),'expected_sha256':sha(pattern/name),'previous_sha256':sha(P/'call-48'/name)}
assert bad_details['4386']['changed_count']==bad_details['4386']['matches_previous_same_offset']==800
assert bad_details['4386']['nonfinite_count']==0 and bad_details['4390']['changed_count']==0
assert len(bad_details['4386']['runs'])==31 and all(x['physical_start']%64==0 and x['bytes'] in (64,128) for x in bad_details['4386']['runs'])
assert sum(x['bytes']==64 for x in bad_details['4386']['runs'])==12 and sum(x['bytes']==128 for x in bad_details['4386']['runs'])==19
ev=[json.loads(x) for x in (P/'phases.jsonl').read_text().splitlines()];assert len(ev)==4896 and all(not x['trace_failed'] for x in ev)
assert [x['phase'] for x in ev if x['exceptional']]==['compare']
before=dict(x.split() for x in (D/'before.vmstat').read_text().splitlines());after=dict(x.split() for x in (D/'after.vmstat').read_text().splitlines());delta={k:int(after[k])-int(before[k]) for k in before if any(s in k for s in ('allocstall','pgscan','pgsteal','oom_kill','compact','pgmajfault'))}
events=[json.loads(x) for x in (P/'vpu/encoder/events.jsonl').read_text().splitlines()];abort=[x for x in events if x['event']=='abort_streamoff'];assert len(abort)==2 and all(x['result']==0 for x in abort)
r={'status':'high_address_VPU_finite_stale_data_failure_preserved','completed_correct':49,'forward_calls':50,'FP32_values_correct_prefix':values,
   'failed_invocation':49,'failed_pattern':1,'failure':(P/'failure.txt').read_text(),'saved_inputs_bitwise':True,'saved_two_outputs':True,
   'outputs':bad_details,'trace':trace,'phase_events':len(ev),'failure_only_late_source_reads':0,
   'counter_limit':'0->11 and isReady do not establish source DDR contents or transfer generation.','source_producer_vs_copy_cache_responsibility':'unresolved',
   'vmstat_delta':delta,'abort_streamoff_successes':2,'normal_drain_LAST_pass':False,'SDK_prefix_chunks_after_release':0,
   'kernel_unchanged':True,'root_cause_resolved':False,'no_hardware_retry':True}
(E/'on.failure-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('49 correct/576240 FP32; inv49 DATA800 stale previous-frame values in31 aligned runs; INDEX4200 correct; no repair/no late reads')
