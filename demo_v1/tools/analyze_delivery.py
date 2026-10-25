"""阶段差值仅在各自单调时钟域内计算；保留未完成阶段，不跨PC/板端减绝对时间。"""
from pathlib import Path
import argparse,json

def stats(values):
    if not values:return None
    v=sorted(values)
    import math
    return {'count':len(v),'mean_ms':sum(v)/len(v),'p95_ms':v[math.ceil(.95*len(v))-1],
            'p99_ms':v[math.ceil(.99*len(v))-1],'max_ms':v[-1]}

def main():
    p=argparse.ArgumentParser();p.add_argument('run',type=Path);p.add_argument('--board-results',type=Path);a=p.parse_args()
    rows=[json.loads(s) for s in (a.run/'host-delivery.jsonl').read_text().splitlines()]
    phases={'Host_original_save':('save_begin','save_end'),'Host_decode_gate':('save_end','decode_end'),
            'Host_ACK_kernel_write':('ack_queued','ack_flushed'),'Host_ACK_to_board_confirmation':('ack_queued','confirmation')}
    report={'Host_rows':len(rows),'Host_phases':{},'Host_slow_save_rows':[],'clock_rule':'Durations within each clock only; ACK is successful OS file-write completion, not per-frame fsync.'}
    for phase,(start,end) in phases.items():
        report['Host_phases'][phase]=stats([(int(r[end+'_ns'])-int(r[start+'_ns']))/1e6 for r in rows if int(r[start+'_ns']) and int(r[end+'_ns'])])
    for r in rows:
        if int(r['save_begin_ns']) and int(r['save_end_ns']) and int(r['save_end_ns'])-int(r['save_begin_ns'])>20_000_000:
            report['Host_slow_save_rows'].append({'invocation':r['invocation'],'save_ms':(int(r['save_end_ns'])-int(r['save_begin_ns']))/1e6})
    if a.board_results:
        b=[json.loads(s) for s in (a.board_results/'delivery-timing.jsonl').read_text().splitlines()]
        report['board_whole_run_summary']=json.loads((a.board_results/'delivery-summary.json').read_text())
        report['board_recent_phases']={}
        for phase,start,end in [('send','send_begin_ns','send_end_ns'),('ACK_wait','ack_begin_ns','ack_end_ns'),('encode','dequeued_ns','encode_end_ns')]:
            report['board_recent_phases'][phase]=stats([(r[end]-r[start])/1e6 for r in b if start in r and r[start] and r[end]])
        report['board_recent_output_backpressure']=[r for r in b if r.get('kind')=='output_backpressure']
        report['scope']='Host full run, board last256 deliveries plus whole-run maxima; stage timestamps are sidecars, wire schema unchanged.'
    (a.run/'delivery-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
