"""Separate input-paced finite rates and service spans on the single board clock."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
def stats(values):
    a=np.asarray(values,dtype=np.float64);assert len(a) and np.isfinite(a).all() and (a>=0).all()
    return dict(count=len(a),mean=float(a.mean()),P95=float(np.percentile(a,95)),maximum=float(a.max()))
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--numeric-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    numeric=json.loads(a.numeric_review.read_text());assert numeric['status']=='live_stage_passed' and numeric['stage']=='load-103'
    file=a.results/'timing.jsonl';rows=[json.loads(x) for x in file.read_text().splitlines()];active=rows[3:];assert len(active)==numeric['measured_consumed']>1
    assert all((a.results/'engine'/name).stat().st_size==0 for name in ['monotonic-spans.jsonl','readiness.jsonl','operator-execution.jsonl'])
    first,last=active[0],active[-1];arrival=(last['arrived_ns']-first['arrived_ns'])/1e6;picture=(last['convert_end_ns']-first['convert_end_ns'])/1e6
    endpoint=((last['convert_end_ns']-last['arrived_ns'])-(first['convert_end_ns']-first['arrived_ns']))/1e6
    assert abs(picture-arrival-endpoint)<1e-6
    service=[(x['verify_end_ns']-x['dequeued_ns'])/1e6 for x in active]
    gaps=[(z['dequeued_ns']-y['verify_end_ns'])/1e6 for y,z in zip(active,active[1:])]
    futureInput=[max(0,z['arrived_ns']-y['verify_end_ns'])/1e6 for y,z in zip(active,active[1:])]
    assert all(g+1e-6>=f for g,f in zip(gaps,futureInput))
    report=dict(status='bounded103_single_clock_rates_and_service_spans_analyzed',timing_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),numeric_review_sha256=hashlib.sha256(a.numeric_review.read_bytes()).hexdigest(),warmups=3,actual_measured_consumed=len(active),received=numeric['sent'],overwritten=numeric['overwritten'],arrival_span_ms=arrival,picture_span_ms=picture,endpoint_latency_change_ms=endpoint,received_sequence_interval_Hz=(last['sequence']-first['sequence'])*1000/arrival,consumed_arrival_interval_Hz=(len(active)-1)*1000/arrival,picture_completion_interval_Hz=(len(active)-1)*1000/picture,strict_original_rate_gate=numeric['whole_5Hz_threshold_met'],service_ms=stats(service),inter_service_gap_ms=stats(gaps),input_not_yet_arrived_portion_ms=stats(futureInput),reciprocal_mean_service_Hz=1000/float(np.mean(service)),reciprocal_is_not_actual_capacity_test=True,slowest=sorted(active,key=lambda x:x['forward_ms'],reverse=True)[:5],old_221ms_spike_threshold_reached=any(x['forward_ms']>=221.6102 for x in rows),PC_board_clocks_subtracted=False,scope='Finite input-paced intervals, not unconstrained saturation capacity or long-term5Hz; no rounding or removal of spikes')
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['actual_measured_consumed','received_sequence_interval_Hz','picture_completion_interval_Hz','strict_original_rate_gate','service_ms','inter_service_gap_ms','old_221ms_spike_threshold_reached']},indent=2))
if __name__=='__main__':main()
