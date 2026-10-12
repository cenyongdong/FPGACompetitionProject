"""Final read-only local identity, original bytes and document link checks."""
import json,re
from pathlib import Path
import mixed_validation_gate as g
from review_model_only_build_base import identities
root=g.ROOT;e=root/'tools/pose-v1/evidence/model-only-20261010-r1';m,b,n=identities(root/'.local/pose-v1-model-only/package-20261010-r1',root/'.local/pose-v1-build/mixed-20261010-model-only-r1')
c=g.load(e/'completion-review.json');assert c['manifest_sha256']==b['package_manifest_sha256'] and c['program_sha256']==b['model_only_binary_sha256'] and c['FP32_compared']==1615700
for name,digest in c['evidence_sha256'].items():assert g.sha(e/name)==digest
for name,digest in c['review_tools_sha256'].items():assert g.sha(root/'tools/pose-v1'/name)==digest
for name,digest in c['archive_sha256'].items():assert g.sha(e/name)==digest
for ck in ['active-checkpoint.json','next-checkpoint.json']:
    x=g.load(e/ck);assert x['completion_sha256']==g.sha(e/'completion-review.json') and not x['active_tests'] and not x['services_running'] and x['SSH_SCP_closed']
new=(root/'tools/pose-v1/model-only-CMakeLists.txt').read_text();entry=new.split('add_executable(pose_model_only_check ',1)[1].split('add_executable(pose_model_only_selftest',1)[0]
assert not any(x in entry for x in ['encoder','render','tcp','rtsp','display','liveMedia','ssl','crypto'])
docs=['ADR/ADR_26.md','tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md','tools/pose-v1/MODEL-ONLY-NEXT-20261010.md','Agents.md','Done.md','PROJECT-PROGRESS.md','DIFFICULTIES.md','REFERENCES.md','ToDoLists.md','ADR/README.md'];checked=0
for rel in docs:
    p=root/rel;s=p.read_text(encoding='utf-8')
    if rel in ['ADR/ADR_26.md','tools/pose-v1/MODEL-ONLY-RESULTS-20261010.md','tools/pose-v1/MODEL-ONLY-NEXT-20261010.md']:part=s
    else:part=s[:s.find('\n\n',s.find('MODEL-ONLY-RESULTS-20261010'))+2]
    for target in re.findall(r'\]\(([^)]+)\)',part):
        if target.startswith(('http:','https:','#')):continue
        assert (p.parent/target.split('#')[0]).exists(),(rel,target);checked+=1
report=dict(status='model_only_final_identity_sources_evidence_links_checked',payloads=n,source_files=len(m['build_files']),frozen_Engine_bridge_CPU_in_manifest=True,no_video_in_new_target=True,local_links_checked=checked,completion_sha256=g.sha(e/'completion-review.json'),documents_sha256={rel:g.sha(root/rel) for rel in docs},additional_tests_executed=False,hardware_accessed=False)
out=e/'final-local-review.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:report[k] for k in ['status','payloads','source_files','local_links_checked']}))
