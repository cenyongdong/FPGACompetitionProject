"""Bounded read-only observation of owned comparison jobs."""
import argparse,json,time
from pathlib import Path

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();start=time.monotonic()
    while time.monotonic()-start<7200:
        rows=[]
        for name in ['finetune-r1','scratch-r1']:
            path=a.root/name
            s=json.loads((a.root/(name+'-status.json')).read_text());v=json.loads((path/'progress.json').read_text())
            h=[json.loads(x) for x in (path/'validation.jsonl').read_text().splitlines()] if (path/'validation.jsonl').exists() else []
            rows.append(dict(arm=name,stage=s['stage'],failed=s.get('failed',False),epoch=v['epoch'],iter=v['iter'],elapsed_s=round(v['elapsed_seconds']),
              lr=max(v['lr']),completed_epochs=len(h),last_top1_mm=round(h[-1]['metrics']['top1_mpjpe'],2) if h else None,
              best_top1_mm=round(min(x['metrics']['top1_mpjpe'] for x in h),2) if h else None))
        print(json.dumps(rows),flush=True)
        if all(x['stage']=='completed' for x in rows) or any(x['failed'] for x in rows):break
        time.sleep(40)
