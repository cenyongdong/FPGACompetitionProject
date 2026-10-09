"""Additional pure-clock gate. No SDK queries or board operations."""
import argparse,json
from pathlib import Path
from review_forward_r2_stage import rows,sha
from analyze_forward_trace import union
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    out=a.results/'results';spans=rows(out/'engine/monotonic-spans.jsonl');timings=rows(out/'timing.jsonl')
    assert (a.results/'exit.txt').read_text().strip()=='0'
    assert (out/'engine/readiness.jsonl').stat().st_size==(out/'engine/operator-execution.jsonl').stat().st_size==0
    assert not any(s['kind']=='runtime.observation' for s in spans)
    assert not (out/'failed-host-inputs').exists()
    assert len(timings)==33 and set(s['invocation'] for s in spans)==set(range(32)) and len(spans)<8192
    for i in range(32):
        group=[s for s in spans if s['invocation']==i]
        assert all(s['frame_id']==timings[i]['transport_id'] for s in group)
        assert sum(s['kind']=='op.host' for s in group)==sum(s['kind']=='op.zg' for s in group)==7
    report=dict(status='pure_timing_no_extra_readiness_queries_verified',invocations=32,records=len(spans),source_sha256=sha(out/'engine/monotonic-spans.jsonl'),readiness_rows=0,operator_log_rows=0,observation_spans=0,normal_path_failure_IO=False,performance_acceptance=False)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if __name__=='__main__':main()
