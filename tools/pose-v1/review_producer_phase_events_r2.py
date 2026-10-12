"""Review bounded phase events and every actual saved prefix, retaining failures."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
R = Path(__file__).resolve().parents[2]
E = R / 'tools/pose-v1/evidence/producer-phase-20261011-r2'
mode = sys.argv[1];assert mode in ('off','on')
D = E / (mode + '-return/run-' + mode);P = D / 'results'
ref = R / 'tools/pose-v1/evidence/producer-reference-20261011-r2/patterns'
load = lambda p: json.loads(p.read_text())
code = int((D / 'exit.txt').read_text());summary = load(P / 'summary.json')
assert (D / 'before.dmesg.txt').read_bytes() == (D / 'after.dmesg.txt').read_bytes()
assert load(P / 'release.json')['remaining_sdk_chunks'] == 0
ev = [json.loads(x) for x in (P / 'phases.jsonl').read_text().splitlines()]
assert ev and len(ev) <= 16384 and all(not x['trace_failed'] for x in ev)
assert all(a['wall_ns'] <= b['wall_ns'] and a['thread_cpu_ns'] <= b['thread_cpu_ns'] for a,b in zip(ev,ev[1:]))
stack = [];spans = []
for x in ev:
    if x['edge'] == 'begin':stack.append(x)
    else:
        a = stack.pop();assert (a['phase'],a['value'],a['invocation']) == (x['phase'],x['value'],x['invocation'])
        spans.append({'phase':x['phase'],'value':x['value'],'invocation':x['invocation'],'begin_ns':a['wall_ns'],'end_ns':x['wall_ns'],
                      'wall_ms':(x['wall_ns']-a['wall_ns'])/1e6,'cpu_ms':(x['thread_cpu_ns']-a['thread_cpu_ns'])/1e6,
                      'minor_faults':x['minor_faults']-a['minor_faults'],'major_faults':x['major_faults']-a['major_faults'],
                      'voluntary_switches':x['voluntary_switches']-a['voluntary_switches'],
                      'involuntary_switches':x['involuntary_switches']-a['involuntary_switches'],'exceptional':x['exceptional']})
assert not stack
forward = [x for x in spans if x['phase']=='forward'];resets = [x for x in spans if x['phase']=='reset']
assert len(forward) == len(resets)
values = 0;rows = []
for i in range(summary['completed']):
    d=P/('call-'+str(i));pattern=ref/('pattern-'+str(i%2));identity=load(d/'identity.json');t=load(d/'trace.json')
    assert identity['invocation']==i and identity['pattern']==i%2
    assert t['before_forward_count']==0 and t['after_ready_count']==11
    assert identity['planned_ns'] <= t['reset_begin_ns'] < identity['planned_ns']+198019801
    for name in ('input-486.f32','input-478.f16','output-4386.f32','output-4390.f32'):
        assert (d/name).read_bytes()==(pattern/name).read_bytes(),(i,name)
        if name.startswith('output'):
            a=np.fromfile(d/name,dtype='<f4');assert np.isfinite(a).all();values+=a.size
    assert load(d/'comparison.json')['saved_before_compare']
    rows.append({'invocation':i,'reset_begin_ns':t['reset_begin_ns'],'forward_us':(t['forward_return_ns']-t['forward_begin_ns'])/1000})
exceptional=[x for x in spans if x['exceptional']]
if code==0:
    assert summary['completed']==100 and summary['all_bitwise'] and len(forward)==100 and not exceptional
else:
    assert not summary['all_bitwise'] and (P/'failure.txt').exists()
    # Also preserve/check any actual complete outputs after a later output-save failure.
    for x in forward:
        d=P/('call-'+str(x['invocation']));pattern=ref/('pattern-'+str(x['invocation']%2))
        for name in ('output-4386.f32','output-4390.f32'):
            if (d/name).exists():assert (d/name).read_bytes()==(pattern/name).read_bytes()
phase_stats={}
for phase in sorted({x['phase'] for x in spans}):
    data=[x for x in spans if x['phase']==phase];wall=np.array([x['wall_ms'] for x in data]);largest=max(data,key=lambda x:x['wall_ms'])
    phase_stats[phase]={'count':len(data),'mean_ms':float(wall.mean()),'p95_ms':float(np.percentile(wall,95)),'max':largest}
leaves=[x for x in spans if x['phase'] not in ('sleep','sdk_call')]
failure=(P/'failure.txt').read_text() if code else None
r={'status':'fixed100_outputs_and_lifecycle_verified' if code==0 else 'phase_failure_prefix_preserved',
   'mode':mode,'exit':code,'calls':summary['completed'],'forward_calls':len(forward),'reset_calls':len(resets),
   'FP32_values':values,'all_saved_inputs_outputs_bitwise':True,'phase_events':len(ev),'phase_stats':phase_stats,
   'largest_non_sleep_non_parent_spans':sorted(leaves,key=lambda x:x['wall_ms'],reverse=True)[:15],
   'exceptional_spans':exceptional,'failure':failure,'SDK_chunks_after_release':0,'kernel_unchanged':True,
   'root_cause_resolved':False,'performance_acceptance':False,'resource_counter_limit':'Interval observations; no syscall/scheduler causality proof.'}
(E/(mode+'.phase-review.json')).write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
if mode=='off' and code==0:
    (E/'off.data-review.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
print(mode,'exit',code,'completed',summary['completed'],'values',values,'events',len(ev),'largest leaf',r['largest_non_sleep_non_parent_spans'][0])
