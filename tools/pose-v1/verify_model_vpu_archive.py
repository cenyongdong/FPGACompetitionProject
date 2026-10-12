"""Verify archive bindings and local documentation after the bounded run ended."""
import json,re
from pathlib import Path
import mixed_validation_gate as g
from review_model_vpu_build_base import identities

root=g.ROOT;e=root/'tools/pose-v1/evidence/model-vpu-20261010-r2'
report=g.load(e/'completion-review.json');checkpoint=g.load(e/'next-checkpoint.json')
assert checkpoint['completion_review_SHA256']==g.sha(e/'completion-review.json')
assert not any(checkpoint[k] for k in ('active_tests','services_running','user_paused')) and checkpoint['SSH_SCP_closed']
assert checkpoint==g.load(e/'active-checkpoint.json') and checkpoint['failed_stage']=='vpu-103'
for rel,digest in report['evidence_SHA256'].items():assert g.sha(e/rel)==digest
for rel,digest in report['archives_SHA256'].items():assert g.sha(e/rel)==digest
m,b,n=identities(root/'.local/pose-v1-model-vpu/package-20261010-r2',root/'.local/pose-v1-build/mixed-20261010-model-vpu-r2')
assert len(m['build_files'])==102 and n==403 and b['model_vpu_binary_sha256']==report['program_SHA256']
docs=['tools/pose-v1/MODEL-VPU-RESULTS-20261010.md','tools/pose-v1/MODEL-VPU-NEXT-20261010.md','tools/pose-v1/MODEL-VPU-RESUME-20261010.md','ADR/ADR_27.md']
links=0
for rel in docs:
    p=root/rel
    for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in href or href.startswith('#'):continue
        target=(p.parent/href.split('#')[0]).resolve();assert target.exists(),str(target);links+=1
agents=(root/'AGENTS.md').read_text(encoding='utf-8');assert '192.168.126.49' in agents and '账号 `root`，密码 `fmsh`' in agents
tools=['ssh_memory_transport.py','review_model_vpu.py','review_model_vpu_startup_failure.py','record_model_vpu_completion.py','update_model_vpu_documents.py','verify_model_vpu_archive.py','run-model-vpu.sh','review_model_only_objects.py','review_model_only_counts.py','review_scratch_video.py']
review=dict(status='final_local_archive_source_bindings_and_links_passed',local_links_checked=links,build_sources_checked=len(m['build_files']),source_payloads_checked=n,completion_review_SHA256=g.sha(e/'completion-review.json'),next_checkpoint_SHA256=g.sha(e/'next-checkpoint.json'),review_tools_SHA256={name:g.sha(root/'tools/pose-v1'/name) for name in tools},documents_SHA256={rel:g.sha(root/rel) for rel in docs+['AGENTS.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','ADR/ADR_02.md','ADR/README.md','tools/pose-v1/README.md']},new_board_operations=False)
p=e/'final-local-review.json';assert not p.exists();p.write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
print(review['status'],links,'links',len(m['build_files']),'sources',n,'payloads')
