"""Final local consistency check; no device operations or repeated tests."""
import json,re
from pathlib import Path
import mixed_validation_gate as g
from review_position_build import identities
root=g.ROOT;e=root/'tools/pose-v1/evidence/plddr-position-20261010-r1';m,b,n=identities(root/'.local/pose-v1-plddr-position/package-20261010-r1',root/'.local/pose-v1-build/mixed-20261010-plddr-position-r1')
c=g.load(e/'completion-review.json');assert c['manifest_sha256']==b['package_manifest_sha256'] and c['program_sha256']==b['position_binary_sha256'] and n==403
for name,digest in c['evidence_sha256'].items():assert g.sha(e/name)==digest
for name,digest in c['review_tools_sha256'].items():assert g.sha(root/'tools/pose-v1'/name)==digest
for name,digest in c['archive_sha256'].items():assert g.sha(e/name)==digest
audit=g.load(e/'manager.acceptance.json')
for name,digest in audit['disassembly_sha256'].items():assert g.sha(e/name)==digest
assert g.sha(e/'ARM-device.h.txt')==audit['header_sha256']
assert g.sha(root/'.local/pose-v1-build/plddr-manager-20261010-r1/build-result.json')==audit['build_result_sha256']
typed=(root/'software/pose_v1/src/typed_scratch_sdk.cpp').read_text();position=(root/'software/pose_v1/src/plddr_position_sdk_r1.cpp').read_text();marker='void SdkScratch::writePattern'
assert typed[typed.index(marker):]==position[position.index(marker):], 'Frozen write/read/copy changed'
for ck in ('next-checkpoint.json','active-checkpoint.json'):
    x=g.load(e/ck);assert x['completion_sha256']==g.sha(e/'completion-review.json') and not x['active_tests'] and not x['services_running'] and x['SSH_SCP_closed']
docs=['ADR/ADR_25.md','tools/pose-v1/PLDDR-POSITION-RESULTS-20261010.md','tools/pose-v1/PLDDR-POSITION-NEXT-20261010.md','Done.md','PROJECT-PROGRESS.md','Agents.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/README.md']
checked=0
for rel in docs:
    p=root/rel;src=p.read_text(encoding='utf-8')
    # New stage documents: all local links must resolve. Large project roots:
    # check newly inserted first entry, leave historical unrelated links alone.
    part=src if rel.startswith(('ADR/ADR_25','tools/pose-v1/PLDDR')) else src[:src.find('\n\n',src.find('PLDDR-POSITION'))+2]
    for target in re.findall(r'\]\(([^)]+)\)',part):
        if target.startswith(('http:','https:','#')):continue
        assert (p.parent/target.split('#')[0]).exists(),(rel,target);checked+=1
report=dict(status='position_final_source_hash_evidence_links_checked',payloads=n,source_files=len(m['build_files']),frozen_write_read_copy_exact=True,completion_sha256=g.sha(e/'completion-review.json'),local_links_checked=checked,documents_sha256={rel:g.sha(root/rel) for rel in docs},new_tests_executed=False,hardware_accessed=False)
out=e/'final-local-review.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','payloads','source_files','local_links_checked']}))
