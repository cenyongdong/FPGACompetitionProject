"""Final local archive/source/link checks; never opens a board or device."""
import json,re
import mixed_validation_gate as g
from review_resident_sequence_build_base import identities
root=g.ROOT;e=root/'tools/pose-v1/evidence/resident-sequence-20261010-r1'
r=g.load(e/'completion-review.json');c=g.load(e/'next-checkpoint.json')
assert g.sha(e/'completion-review.json')==c['completion_review_SHA256'] and c==g.load(e/'active-checkpoint.json')
assert not any(c[k] for k in ('user_paused','active_tests','services_running')) and c['SSH_SCP_closed']
for name,digest in r['evidence_SHA256'].items():assert g.sha(e/name)==digest
for name,digest in r['archive_SHA256'].items():assert g.sha(e/name)==digest
m,b,n=identities(root/'.local/pose-v1-resident-sequence/package-20261010-r1',root/'.local/pose-v1-build/mixed-20261010-resident-sequence-r1')
assert n==403 and len(m['build_files'])==108 and b['resident_binary_sha256']==r['program_SHA256']
assert r['correct_calls']==107 and r['FP32_compared']==1615700 and r['VPU_synthetic_images']==518 and r['agent_compactions']==1
docs=['tools/pose-v1/RESIDENT-SEQUENCE-RESULTS-20261010.md','tools/pose-v1/RESIDENT-SEQUENCE-NEXT-20261010.md','ADR/ADR_28.md'];links=0
for rel in docs:
    p=root/rel
    for href in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
        if '://' in href or href.startswith('#'):continue
        target=(p.parent/href.split('#')[0]).resolve();assert target.exists(),str(target);links+=1
tools=['create_resident_sequence_sources.py','prepare_resident_sequence.py','Build-ResidentSequence.ps1','review_resident_sequence_build_base.py','run_resident_sequence_native.py','resident_sequence_transfer.py','run-resident-sequence.sh','review_resident_sequence.py','create_resident_count_review.py','review_resident_counts.py','record_resident_sequence_completion.py','update_resident_sequence_documents.py','verify_resident_sequence_archive.py','ssh_memory_transport.py']
review=dict(status='final_local_resident_archive_and_source_links_passed',local_links_checked=links,source_payloads_checked=n,build_sources_checked=108,review_tools_SHA256={name:g.sha(root/'tools/pose-v1'/name) for name in tools},document_SHA256={rel:g.sha(root/rel) for rel in docs+['Done.md','Agents.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','ADR/ADR_02.md','ADR/README.md','tools/pose-v1/README.md']},completion_review_SHA256=g.sha(e/'completion-review.json'),next_checkpoint_SHA256=g.sha(e/'next-checkpoint.json'),tool_failure_history_SHA256=g.sha(e/'tool-failure-history.json'),new_board_tests=False)
p=e/'final-local-review.json';assert not p.exists();p.write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8',newline='\n')
print(review['status'],links,'links',108,'sources',n,'payloads')
