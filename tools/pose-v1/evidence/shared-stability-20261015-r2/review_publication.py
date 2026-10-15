"""Preserve LF for edited documents, audit links and hash final publication."""
from pathlib import Path
import hashlib,json,re,subprocess
E=Path(__file__).resolve().parent;R=E.parents[3]
docs=[R/'PROJECT-PROGRESS.md',R/'Done.md',R/'DIFFICULTIES.md',R/'REFERENCES.md',R/'ADR/ADR_48.md',E/'REPORT.md']
for p in docs:
 s=p.read_text(encoding='utf-8')
 if p==E/'REPORT.md':
  s=s.replace('无重启、规整、drop_caches','无重启、主动规整、drop_caches').replace('未清缓存、规整、重启','未清缓存、主动规整、重启')
 p.write_text(s,encoding='utf-8',newline='\n')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
revision=json.loads((E/'documentation-revision.json').read_text(encoding='utf-8'))
for item in revision['files']:item['after_sha256']=sha(Path(item['path']))
assert revision['files'][0]['before_sha256']==revision['files'][0]['after_sha256']
(E/'documentation-revision.json').write_text(json.dumps(revision,indent=2)+'\n',encoding='utf-8',newline='\n')
missing=[];checked=0
for p in docs:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  target=target.strip('<>').split('#',1)[0]
  if not target or re.match(r'^[a-zA-Z]+://',target):continue
  if target=='completion-review.json' and p==E/'REPORT.md':continue
  checked+=1
  if not (p.parent/target).exists():missing.append(dict(file=str(p),target=target))
new_missing=[]
for item in missing:
 p=Path(item['file']);rel=p.relative_to(R).as_posix()
 old=subprocess.check_output(['git','show','HEAD:'+rel],cwd=R).decode('utf-8')
 item['already_in_HEAD']=item['target'] in old
 if not item['already_in_HEAD']:new_missing.append(item)
report=dict(links_checked=checked,pre_existing_missing_or_parenthesis_parser_limit=missing,new_missing=new_missing,LF_preserved=True,
 note='Historical references are recorded without changing old evidence or broadening this task. Parentheses in one existing path exceed this simple link parser.')
(E/'publication-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
print(json.dumps(report,indent=2))
assert not new_missing,'Resolve new publication links before completion'
