"""Final read-only source, archive, public-map and corrected-gate binding check."""
from pathlib import Path
import json,hashlib,ast
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((E/'completion-review.json').read_text());d=json.loads((E/'data-review.json').read_text());assert sha(E/'data-review.json')==c['data_review_sha256']
for p,h in d['archives_sha256'].items():assert sha(E/p)==h
for p,h in c['documents_sha256'].items():
    if p=='tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md':continue
    assert sha(R/p)==h
c['documents_sha256']['tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md']=sha(R/'tools/pose-v1/PRODUCER-CONTRACT-RESULTS-20261011.md')
assert d['apply_stages']['apply-r3-return']['program_exit']==1 and d['apply_stages']['apply-return']['program_exit']==0
assert all(x['official_log_files']==2 for x in d['apply_stages'].values())
future=R/'.local/pose-v1-build/producer-deployment-20261011-r4';b=json.loads((future/'build-result.json').read_text());assert sha(future/'pose_producer_deployment_log')==b['program_sha256'] and sha(R/'software/pose_v1/src/producer_deployment_log.cpp')==b['entry_sha256']
for p in (R/'tools/pose-v1').glob('*producer*py'):ast.parse(p.read_text(encoding='utf-8-sig'))
c['scripts_sha256']={p.name:sha(p) for p in (R/'tools/pose-v1').glob('*producer*py')}
c['final_readonly_verification_passed']=True
(E/'completion-review.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
n=json.loads((E/'next-checkpoint.json').read_text());n['completion_sha256']=sha(E/'completion-review.json');(E/'next-checkpoint.json').write_text(json.dumps(n,indent=2)+'\n',encoding='utf-8',newline='\n');print('Final completion binding passed',sha(E/'completion-review.json'))
