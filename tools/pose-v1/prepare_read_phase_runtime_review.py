"""Separate runtime adapter: use pinned original-three and expanded captures."""
from pathlib import Path
import mixed_validation_gate as g
r=g.ROOT;p=r/'tools/pose-v1/review_read_phase_runtime_r2.py';assert not p.exists()
s=(r/'tools/pose-v1/review_read_phase.py').read_text(encoding='utf-8')
old="gold=g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1/results/content';index=[json.loads(x) for x in (gold/'index.jsonl').read_text().splitlines()]\n            matches=[x for x in index if x['case']==case and x['op_id']==192 and x['slot']==1 and x['kind']=='bridge_input'];assert matches\n            baseline=(gold/matches[0]['file']).read_bytes();assert all((gold/x['file']).read_bytes()==baseline for x in matches)"
new="""baseline_values=[]
            for run in [g.ROOT/'tools/pose-v1/evidence/mixed-20261006-frame-state-r6/mixed-three',g.ROOT/'tools/pose-v1/evidence/runtime-20261007-r2/n1']:
                g.verify(run);gold=run/'results/content';index=[json.loads(x) for x in (gold/'index.jsonl').read_text().splitlines()]
                matches=[x for x in index if x['case']==case and x['op_id']==192 and x['slot']==1 and x['kind']=='bridge_input']
                baseline_values.extend((gold/x['file']).read_bytes() for x in matches)
            assert baseline_values;baseline=baseline_values[0];assert all(b==baseline for b in baseline_values)"""
assert s.count(old)==1;s=s.replace(old,new,1);p.write_text(s,encoding='utf-8',newline='\n')
print('Independent runtime baseline adapter prepared; no data changed')
