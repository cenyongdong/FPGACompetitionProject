"""Verify completion; repair only the empty inventory selection, preserving it."""
from pathlib import Path
import hashlib,json,shutil,ast
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-reference-20261011-r2';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((E/'completion-review.json').read_text())
if c['frozen_software_sources_unchanged']==0:
    old=E/'completion-before-source-audit.json';assert not old.exists();shutil.copyfile(E/'completion-review.json',old)
    manifest=json.loads((R/'.local/pose-v1-read-phase/package-20261011-r3/manifest.json').read_text())
    hashes={p:v['sha256'] for p,v in manifest['build_files'].items() if p.startswith('software/')}
    assert len(hashes)>100
    for p,h in hashes.items():assert sha(R/p)==h
    c['frozen_software_sources_unchanged']=len(hashes);c['frozen_software_hashes']=hashes
    c['source_inventory_correction']={'previous_completion_sha256':sha(old),'reason':'sources field contains tooling; software hashes are build_files entries; initial empty filter preserved','physical_rerun':False}
    p=R/'ADR/ADR_38.md';p.write_text(p.read_text(encoding='utf-8')+'\n归档首次从manifest的工具sources字段筛选软件得到空项；发现后保留原completion，用build_files真实清单核对'+str(len(hashes))+'份冻结软件，全部哈希不变，增加非空断言。仅本机证据门检修正，没有模型或板测重跑。\n',encoding='utf-8',newline='\n')
    c['documents']['ADR/ADR_38.md']=sha(p)
    c['source_hashes']['tools/pose-v1/archive_producer_reference.py']=sha(R/'tools/pose-v1/archive_producer_reference.py')
    c['source_hashes']['tools/pose-v1/verify_producer_reference_completion.py']=sha(Path(__file__))
    (E/'completion-review.json').write_text(json.dumps(c,indent=2)+'\n',encoding='utf-8',newline='\n')
for p,h in c['documents'].items():assert sha(R/p)==h,('document',p)
for p,h in c['source_hashes'].items():
    assert sha(R/p)==h,('source',p)
    if p.endswith('.py'):ast.parse((R/p).read_text(encoding='utf-8-sig'))
for p,h in c['frozen_software_hashes'].items():assert sha(R/p)==h
for p,h in c['reviews'].items():assert sha(E/p)==h
for p,h in c['archives'].items():assert sha(E/p)==h
assert sha(E/'next-checkpoint.json')==c['checkpoint_sha256']
assert c['new_physical_forwards']==0 and c['kernel_unchanged'] and c['compactions']==0 and c['connections_closed']
assert c['reference_FP32_values']==23520 and c['replay_bitwise_equal']
print('Completion verified, frozen software',c['frozen_software_sources_unchanged'],'SHA256',sha(E/'completion-review.json'))
