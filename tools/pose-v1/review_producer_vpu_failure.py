"""Preserve pacing failure; independently verify only actually saved prefix."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-vpu-20261011-r2';D=E/'on-return/run-on';P=D/'results';ref=R/'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
assert (D/'exit.txt').read_text().strip()=='1' and (P/'failure.txt').read_text()=='Call exhausted slot; no catch-up'
assert (D/'before.dmesg.txt').read_bytes()==(D/'after.dmesg.txt').read_bytes()
s=json.loads((P/'summary.json').read_text());assert s['completed']==82 and s['requested']==100 and not s['all_bitwise']
assert json.loads((P/'release.json').read_text())['remaining_sdk_chunks']==0
rows=[];values=0
for i in range(82):
    d=P/('call-'+str(i));pattern=ref/('pattern-'+str(i%2));ident=json.loads((d/'identity.json').read_text());t=json.loads((d/'trace.json').read_text())
    assert ident['invocation']==i and ident['pattern']==i%2 and t['before_forward_count']==0 and t['after_ready_count']==11
    for name in ('input-486.f32','input-478.f16','output-4386.f32','output-4390.f32'):
        assert (d/name).read_bytes()==(pattern/name).read_bytes()
        if name.startswith('output'):a=np.fromfile(d/name,dtype='<f4');assert np.isfinite(a).all();values+=a.size
    assert json.loads((d/'comparison.json').read_text())['saved_before_compare']
    rows.append({'invocation':i,'planned_ns':ident['planned_ns'],'sample_ns':ident['actual_start_ns'],'before_reset_ns':t['reset_begin_ns'],'pre_reset_gap_ms':(t['reset_begin_ns']-ident['actual_start_ns'])/1e6,'forward_us':(t['forward_return_ns']-t['forward_begin_ns'])/1000,'copy_us':[(r['copy_end_ns']-r['copy_begin_ns'])/1000 for r in t['reads']],'owned_end_ns':t['reads'][-1]['owned_end_ns'],'call_to_owned_ms':(t['reads'][-1]['owned_end_ns']-ident['actual_start_ns'])/1e6})
assert not (P/'call-82').exists() and values==964320
last=rows[-1];assert last['pre_reset_gap_ms']>1763 and last['forward_us']<500 and max(last['copy_us'])<120
obs=[json.loads(x) for x in (P/'vpu-ioctl.jsonl').read_text().splitlines()];assert len(obs)==1628 and len({x['thread'] for x in obs})==1
assert all(a['begin_ns']<=a['end_ns']<=b['begin_ns'] for a,b in zip(obs,obs[1:]))
gap=max((b['begin_ns']-a['end_ns'],a['ordinal'],b['ordinal']) for a,b in zip(obs,obs[1:]));longest=max(x['end_ns']-x['begin_ns'] for x in obs)
life=[json.loads(x) for x in (P/'lifecycle.jsonl').read_text().splitlines()];assert [x['event'] for x in life]==['VPU_actual_capture','SDK_initialized','fixed_sequence_started','workers_joined','SDK_destroyed']
assert life[-2]['time_ns']<=life[-1]['time_ns']
encoder=[json.loads(x) for x in (P/'vpu/encoder/events.jsonl').read_text().splitlines()];abort=[x for x in encoder if x['event']=='abort_streamoff'];assert len(abort)==2 and all(x['result']==0 for x in abort)
before=dict(x.split() for x in (D/'before.vmstat').read_text().splitlines());after=dict(x.split() for x in (D/'after.vmstat').read_text().splitlines());delta={k:int(after[k])-int(before[k]) for k in before if any(v in k for v in ('allocstall','pgscan','pgsteal','compact','oom_kill','pgmajfault'))}
r={'status':'pacing_failure_preserved82_outputs_correct_not100_pass','stage_exit':1,'completed':82,'requested':100,'FP32_values_verified':values,'all_saved_outputs_bitwise':True,'all_saved_finite':True,'failed_invocation':81,'failure':'Call exhausted slot; no catch-up','last_invocation':last,'frames':rows,'unobserved_pre_reset_components':['directory/input/identity saves','SDK Host input validation/allocation/write','thread scheduling'],'ioctl_records':len(obs),'largest_ioctl_gap_ns':gap[0],'largest_ioctl_gap_between_ordinals':gap[1:],'largest_ioctl_call_ns':longest,'vmstat_delta':delta,'aborted_streamoff_successes':2,'SDK_chunks_after_release':0,'stage_kernel_unchanged':True,'no_normal_drain_LAST_pass':True,'root_cause_resolved':False,'no_hardware_retry':True}
(E/'on.failure-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n');print('on prefix82/964320 FP32 exact; inv81 pre-reset gap',last['pre_reset_gap_ms'],'ms; root unresolved, no rerun')
