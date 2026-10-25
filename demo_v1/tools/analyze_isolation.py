"""Independent evidence comparison; never edits actual values or retries a load."""
from pathlib import Path
import argparse,json,struct,math

def main():
    p=argparse.ArgumentParser();p.add_argument('board_root',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    root=a.board_root
    static=json.loads((root/'run-static-control/results/summary.json').read_text())
    ledger=json.loads((root/'isolation-budget.json').read_text())
    report={'static':static,'budget':ledger,'static_first_anomaly':(root/'run-static-control/results/first-original.bin').exists()}
    live=root/'run-live-isolation/results'
    if live.exists():
        oracle=json.loads((live/'index-oracle/summary.json').read_text());report['oracle']=oracle
        comparisons=[]
        for invocation in oracle['recent']:
            topk=(live/f'index-oracle/{invocation}.topk.f32').read_bytes()
            expected=b''.join(topk[i:i+4]*42 for i in range(0,len(topk),4))
            actual=(live/f'copy-observations/{invocation}.input1.f32').read_bytes()
            words=struct.unpack('<4200f',actual)
            comparisons.append({'invocation':invocation,'differing_words':sum(actual[i:i+4]!=expected[i:i+4] for i in range(0,len(actual),4)),
                                'illegal_indices':sum(not math.isfinite(x) or x<0 or x>=180 or x!=math.trunc(x) for x in words)})
        report['independent_recent_comparisons']=comparisons
        rows=[json.loads(x) for x in (live/'copy-observations/metadata.jsonl').read_text().splitlines()]
        report['recent_metadata_rows']=len(rows)
        report['additional_device_queries']=sorted(set(x.get('additional_device_queries') for x in rows))
        report['failed_first_Host_exists']=(live/'failed-host-inputs').exists()
        report['failure']=json.loads((live/'failure.json').read_text()) if (live/'failure.json').exists() else None
        report['complete_summary']=json.loads((live/'summary.json').read_text()) if (live/'summary.json').exists() else None
    report['strict_DMA_vs_cache_vs_NPU_attribution_available']=False
    report['reason']='No exposed passive kernel tracing or independently verified hardware completion/visibility contract. API return and ready/count alone do not prove it.'
    if a.output.exists():raise ValueError('Preserve prior analysis')
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
