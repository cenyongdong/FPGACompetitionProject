"""Compact read-only status for the two managed comparison arms."""
import argparse,json
from pathlib import Path

def read(path):return json.loads(path.read_text()) if path.exists() else None
def lines(path):return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();result={}
    for name in ['finetune-r1','scratch-r1']:
        r=a.root/name;status=read(a.root/(name+'-status.json')) or {};progress=read(r/'progress.json') or {};history=lines(r/'validation.jsonl');lr=lines(r/'learning-rate-decisions.jsonl');baseline=read(r/'baseline.json') or {}
        v=dict(stage=status.get('stage'),failed=status.get('failed',False),error=status.get('error'),gpu=status.get('gpu'),
          epoch=progress.get('epoch'),step=progress.get('iter'),elapsed_seconds=round(progress.get('elapsed_seconds',0),1),lr=progress.get('lr'),
          baseline_top1_mm=baseline.get('metrics',{}).get('top1_mpjpe'),
          validation_top1_mm=[round(x['metrics']['top1_mpjpe'],3) for x in history],
          latest_loss=progress.get('metrics',{}).get('loss'),peak_GiB=round(progress.get('cuda_peak',0)/1024**3,2),
          last_lr_reason=lr[-1].get('reason') if lr else None,
          full_validation=read(r/'full-validation.json'),held_out_test=read(r/'held-out-test.json'),best_checkpoint=status.get('best_checkpoint'))
        result[name]=v
    print(json.dumps(result,indent=2,allow_nan=False))
