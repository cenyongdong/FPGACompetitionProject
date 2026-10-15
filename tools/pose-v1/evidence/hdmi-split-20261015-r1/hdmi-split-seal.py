from pathlib import Path
import hashlib,json,re,shutil
R=Path('D:/FPGACompetitionProject');C=R/'FPGA/hdmi_candidate'
E=R/'tools/pose-v1/evidence/hdmi-split-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
for name in ('hdmi-split-start.py','hdmi-fix-clock-literal.py','hdmi-split-finish.py','hdmi-split-seal.py'):
 shutil.copyfile(R/'.local'/name,E/name)
rev={}
for b in (E/'before').rglob('*.md'):
 rel=b.relative_to(E/'before');p=R/rel
 rev[rel.as_posix()]={'before_sha256':sha(b),'after_sha256':sha(p),'changed':sha(b)!=sha(p)}
save(E/'documentation-revision.json',rev)
shutil.copytree(C,E/'candidate-source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for tag in ('hdmi-candidate-sim-20261015-r6','hdmi-candidate-sim-20261015-r7',
            'hdmi-tmds-literal-20261015-r1','hdmi-tmds-literal-20261015-r2',
            'hdmi-tmds-literal-20261015-r3','hdmi-tmds-literal-20261015-r4'):
 d=R/'tools/pose-v1/evidence'/tag
 assert not (d/'files.sha256.json').exists()
 save(d/'files.sha256.json',{p.relative_to(d).as_posix():sha(p) for p in d.rglob('*') if p.is_file()})
links=[]
for p in (C/'README.md',C/'RESUME.md',C/'INTEGRATION.md',E/'REPORT.md'):
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  dest=(p.parent/target.split('#')[0]).resolve()
  assert dest.is_file(),(p,target)
  links.append({'file':str(p),'target':str(dest),'exists':True})
save(E/'local-link-review.json',links)
proc=json.loads((E/'process-inventory.json').read_text(encoding='utf-8-sig'))
assert proc['processes']==[], 'Unexpected tool still running; inspect ownership before ending'
save(E/'files.sha256.json',{p.relative_to(E).as_posix():sha(p) for p in E.rglob('*') if p.is_file()})
print(json.dumps({'sealed':True,'document_revisions':len(rev),'links_checked':len(links),
 'new_batches':['r6 core PASS','r7 pixel PASS','TMDS Lite r4 PASS'],
 'extra_UFAMILY_diagnostic':'preserved failure, not expanded to Lite', 'background_processes':proc['processes']}))
