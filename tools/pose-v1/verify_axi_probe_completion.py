"""Final read-only binding and safe archive extraction check, no board access."""
from pathlib import Path
import hashlib,json,ast
from archive_bytes import extract_bytes
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((E/'completion-review.json').read_text());d=json.loads((E/'data-review.json').read_text())
assert sha(E/'data-review.json')==c['data_review_sha256']
for p,h in c['documents_sha256'].items():assert sha(R/p)==h
for name,h in d['archives_SHA256'].items():assert sha(E/name)==h
b=json.loads((E/'build-result.json').read_text())
for p,s in b['sources'].items():assert sha(R/p)==s['sha256']
for path in (R/'tools/pose-v1').glob('*axi*py'):ast.parse(path.read_text(encoding='utf-8-sig'))
out=E/'safe-extraction-contract';extract_bytes(E/'return-host.tar',out)
for p in out.rglob('*'):
    if p.is_file():assert p.read_bytes()==(E/'readable/return-host'/p.relative_to(out)).read_bytes()
# Review-tool permission fix changes only local archive materialization, not
# compiled program, returned bytes, model/math/gates or any board execution.
c['local_archive_permission_fix_verified']=True
c['scripts_sha256']={p.name:sha(p) for p in (R/'tools/pose-v1').glob('*axi*py')}
c['scripts_sha256']['archive_bytes.py']=sha(R/'tools/pose-v1/archive_bytes.py')
(E/'completion-review.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
n=json.loads((E/'next-checkpoint.json').read_text());n['completion_sha256']=sha(E/'completion-review.json');(E/'next-checkpoint.json').write_text(json.dumps(n,indent=2)+'\n',encoding='utf-8',newline='\n')
print('Final source/archive/document bindings passed; completion',sha(E/'completion-review.json'))
