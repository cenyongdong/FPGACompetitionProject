"""Rank exact bad-byte blocks against frozen captures; pattern evidence only."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
import mixed_validation_gate as g
def main():
    p=argparse.ArgumentParser();p.add_argument('--results',type=Path,required=True);p.add_argument('--gold-review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    review=g.load(a.gold_review);case=review['case'];bad=a.results/'failed-invocation-inputs/op192.slot1.f32'
    ref=g.ROOT/review['records'][-1]['golden_path'];raw=bad.read_bytes();aa=np.frombuffer(raw,'<u4');bb=np.frombuffer(ref.read_bytes(),'<u4');changed=np.flatnonzero(aa!=bb)
    ranges=[]
    for i in changed:
        if ranges and i==ranges[-1][1]:ranges[-1][1]+=1
        else:ranges.append([int(i),int(i)+1])
    root=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1/results/content'
    rows=[json.loads(x) for x in (root/'index.jsonl').read_text().splitlines()]
    captures=[(v,(root/v['file']).read_bytes()) for v in rows if v['kind'] in ('bridge_input','bridge_result')]
    previous=(a.results/'failed-invocation-inputs/op192.slot0.f32').read_bytes()
    blocks=[]
    for begin,end in ranges:
        block=raw[begin*4:end*4];matches=[]
        for v,blob in captures:
            offset=blob.find(block)
            if offset>=0 and offset%4==0:matches.append(dict(case=v['case'],kind=v['kind'],op_id=v['op_id'],slot=v['slot'],offset_FP32=offset//4,same_case=v['case']==case))
        blocks.append(dict(range_FP32=[begin,end],bytes=len(block),mod256=(begin*4)%256,equals_previous_copy_same_offset=block==previous[begin*4:end*4],matches=matches))
    report=dict(status='exact_bad_blocks_ranked_pattern_not_origin_proof',case=case,changed_FP32=len(changed),changed_ranges=len(ranges),blocks_found_in_same_case=sum(any(x['same_case'] for x in v['matches']) for v in blocks),all_bad_blocks_found_somewhere=all(v['matches'] for v in blocks),all_changed_bytes_equal_previous_copy_same_offset=all(v['equals_previous_copy_same_offset'] for v in blocks),previous_copy_sha256=hashlib.sha256(previous).hexdigest(),root_cause_proven=False,actual_sha256=g.sha(bad),gold_sha256=g.sha(ref),blocks=blocks)
    a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='blocks'}))
if __name__=='__main__':main()
