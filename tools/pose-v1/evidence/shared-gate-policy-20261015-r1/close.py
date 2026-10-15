"""Freeze the implemented policy and failed bounded validation; preserve old evidence."""
from pathlib import Path
import hashlib,json,re,subprocess
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
PREV=R/'tools/pose-v1/evidence/shared-graph-board-20261015-r1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

previous=load(PREV/'delivery-files.json')
assert all(sha(Path(n))==v['sha256'] for n,v in previous.items())
revisions=[]
for v in load(E/'documentation-before.json'):
    p=Path(v['Path'])
    revisions.append(dict(path=str(p),before_sha256=v['Hash'].lower(),after_sha256=sha(p),
        changed=sha(p)!=v['Hash'].lower()))
revisions.append(dict(path=str(R/'ADR/ADR_48.md'),before_sha256=None,after_sha256=sha(R/'ADR/ADR_48.md'),changed=True))
save(E/'documentation-revision.json',dict(reason='Explicit user approval of 3mm shared FP16 pose gate; record hypothesis as unverified and actual third-frame failure',
    prior_delivery_entries_verified_unchanged=len(previous),historical_completion_ledgers_rewritten=False,
    changes=revisions))
a=load(E/'analysis.json')
assert a['accepted_frames']==2 and a['rejected_frames']==1 and a['board_exit']==1
assert a['max_joint_delta_mm']>3 and not a['physical_bias_cause_proven']
assert a['SDK_BOOT_after_identity_unchanged'] and a['no_task_process_remains'] and a['FPAI_final_status']=='exited'
assert load(E/'build-exit.json')['exit']==0
assert '12 numerical gate' in (E/'gate-selftest.txt').read_text(encoding='utf-8-sig')
report=E/'REPORT.md'
for md in [report,R/'ADR/ADR_48.md',R/'tools/pose-v1/shared-output-gate/README.md']:
    missing=[]
    for target in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8')):
        if '://' not in target and not (md.parent/target.split('#')[0]).exists():missing.append(target)
    assert not missing,(md,missing)
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True)
(E/'git-diff-check.txt').write_bytes(diff.stdout+diff.stderr);assert diff.returncode==0
records={}
for base in [E,R/'tools/pose-v1/shared-output-gate']:
    for p in sorted(base.rglob('*')):
        if p.is_file() and p.name not in ('delivery-files.json','completion-review.json'):
            records[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
for p in [R/'ADR/ADR_48.md']:
    records[str(p)]=dict(bytes=p.stat().st_size,sha256=sha(p))
save(E/'delivery-files.json',records)
save(E/'completion-review.json',dict(status='policy_implemented_documented_and_retested_third_frame_exceeds_3mm',
    user_approved_max_joint_mm=3.0,policy_implementation='complete',documentation='complete',
    host_boundary_checks=12,ARM_build_exit=0,actual_inferences=3,accepted=2,rejected=1,
    board_exit=1,maximum_joint_delta_mm=a['max_joint_delta_mm'],whole_candidate_acceptance=False,
    original_failure_preserved=True,previous_delivery_entries_unchanged=len(previous),
    threshold_automatically_increased=False,automatic_retry=False,physical_bias_proven=False,
    model_raw_SDK_BOOT_formal_demo_changed=False,old_DATA_investigation_resumed=False,
    board_cleanup_verified=True,FPAI_stopped=True,report=str(report),report_sha256=sha(report),
    delivery_files=len(records),delivery_manifest_sha256=sha(E/'delivery-files.json')))
print(json.dumps(dict(status='policy complete; board candidate still rejected',files=len(records),report=str(report)),ensure_ascii=False))
