"""Bounded monotonic spans, non-additive attribution and epoch uncertainty."""
import argparse,json
from pathlib import Path
import numpy as np
from review_forward_stage import rows,sha,stats

def union(intervals):
    total=0;end=0
    for a,b in sorted(intervals):
        assert 0<=a<=b
        total+=max(0,b-max(a,end));end=max(end,b)
    return total

def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--allow-failure',action='store_true');a=p.parse_args();assert not a.output.exists()
    r=a.results;out=r/'results';timings=rows(out/'timing.jsonl');spans=rows(out/'engine/monotonic-spans.jsonl');display=rows(out/'display-timing.jsonl');packets=rows(out/'packets.jsonl')
    assert len(spans)<8192 and len(timings)<=33
    count=min(len(timings),32)
    if a.allow_failure:
        assert (r/'exit.txt').read_text().strip()=='1' and count>0
        assert set(range(count))<=set(x['invocation'] for x in spans)<=set(range(count+1))
    else:
        assert len(timings)>=32 and set(x['invocation'] for x in spans)==set(range(32))
    assert not json.loads((out/'engine/sdk-profile-setting.json').read_text())['enabled']
    analyzed=[]
    for i in range(count):
        t=timings[i];group=[s for s in spans if s['invocation']==i]
        assert all(s['frame_id']==t['transport_id'] and 0<=s['begin_ns']<=s['end_ns'] for s in group)
        def of(kind):return [s for s in group if s['kind']==kind]
        assert len(of('runtime.forward'))==len(of('runtime.total'))==1
        assert len(of('op.host'))==len(of('op.zg'))==7
        f=of('runtime.forward')[0];duration=f['end_ns']-f['begin_ns']
        assert abs(duration/1e6-t['forward_ms'])<.2
        categories={}
        for kind in sorted(set(s['kind'] for s in group)):
            selected=of(kind);categories[kind]=dict(records=len(selected),sum_ms=sum(s['end_ns']-s['begin_ns'] for s in selected)/1e6,union_ms=union([(s['begin_ns'],s['end_ns']) for s in selected])/1e6)
        for op in (188,192,437,582,649):
            assert any(s['kind']=='bridge.cpu' and s['op_id']==op for s in group)
        # Engine epoch lies inside the external call. Span-end is before return.
        lo=t['process_begin_ns'];hi=t['process_end_ns']-max(s['end_ns'] for s in group)
        assert hi>=lo
        f_start=(lo+f['begin_ns'],hi+f['begin_ns']);f_end=(lo+f['end_ns'],hi+f['end_ns'])
        definite=sum(d['render_begin_ns']<f_end[0] and d['convert_end_ns']>f_start[1] for d in display)
        possible=sum(d['render_begin_ns']<f_end[1] and d['convert_end_ns']>f_start[0] for d in display)
        captured_definite=sum(f_start[1]<=x['capture_ns']<=f_end[0] for x in packets)
        analyzed.append(dict(invocation=i,case=t['case'],forward_ms=duration/1e6,epoch_uncertainty_ns=hi-lo,categories=categories,display_definite_overlap=definite,display_possible_overlap=possible,capture_callbacks_definitely_inside_forward=captured_definite))
    kinds=sorted(set(k for f in analyzed for k in f['categories']))
    aggregate={k:stats([f['categories'].get(k,dict(union_ms=0))['union_ms'] for f in analyzed]) for k in kinds}
    report=dict(status='failed_run_partial_trace_only' if a.allow_failure else 'bounded_forward_trace_analyzed',traced_invocations=count,records=len(spans),source_sha256={str(p.relative_to(r)):sha(p) for p in (out/'timing.jsonl',out/'engine/monotonic-spans.jsonl',out/'display-timing.jsonl',out/'packets.jsonl')},frames=analyzed,union_ms_stats=aggregate,slowest=sorted(analyzed,key=lambda f:f['forward_ms'],reverse=True)[:5],performance_acceptance=False,ZG_span_is_pure_NPU_time=False,categories_overlap_do_not_sum=True,old_spike_reproduction_threshold_ms=221.6102,old_spike_threshold_reached=any(f['forward_ms']>=221.6102 for f in analyzed))
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(records=len(spans),slowest=[(f['invocation'],f['forward_ms']) for f in report['slowest']],aggregate=aggregate),indent=2))
if __name__=='__main__':main()
