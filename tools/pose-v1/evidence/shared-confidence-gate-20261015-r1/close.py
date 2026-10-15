"""Freeze the confidence-scoped implementation and offline re-evaluation only."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess,tarfile
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
S=R/'.local/shared-confidence-source-20261015-r1';D=R/'.local/shared-confidence-delivery-20261015-r1'
PREV=R/'tools/pose-v1/evidence/shared-gate-policy-20261015-r1'
MOD=R/'tools/pose-v1/shared-output-gate'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

a=load(E/'analysis.json');assert a['accepted_under_new_policy']==3 and a['new_board_inferences']==0
assert a['original_board_run_exit']==1 and a['max_checked_joint_delta_mm']==0.9765625
for n,h in load(E/'source-manifest.json')['files'].items():assert sha(S/n)==h,n
assert sha(S/'shared_output_gate.hpp')==sha(MOD/'shared_output_gate.hpp')
for f in ('selftest-build-exit.json','replay-build-exit.json','build-configure-exit.json','build-exit.json'):
    assert load(E/f)['exit']==0,f
assert '21 numerical gate' in (E/'selftest.txt').read_text(encoding='utf-8-sig')
assert (E/'docker-final-state.txt').read_text(encoding='utf-8-sig').strip()=='exited'

old=load(PREV/'delivery-files.json');evidence_entries={n:h for n,h in old.items() if PREV in Path(n).parents}
assert all(sha(Path(n))==h['sha256'] for n,h in evidence_entries.items())
first=load(R/'tools/pose-v1/evidence/shared-graph-board-20261015-r1/delivery-files.json')
assert all(sha(Path(n))==h['sha256'] for n,h in first.items())
binary=D/'pose_shared_timing';b=binary.read_bytes()
assert b[:6]==b'\x7fELF\x02\x01' and int.from_bytes(b[18:20],'little')==183
p=load(R/'.local/shared-gate-delivery-20261015-r1/package.json')
p.update(status='confidence_scoped_package_prepared_not_deployed',binary_sha256=sha(binary),
    source_manifest_sha256=sha(D/'source-manifest.json'),source_directory=str(S),
    strict_comparison='All100 scores and input bitwise; only reference FP32 score>0.2f candidates joint deltas<=3mm; finite checks for all',
    policy=load(E/'policy.json'),expected_frames=3)
p['files']={f.relative_to(D).as_posix():sha(f) for f in sorted(D.rglob('*')) if f.is_file()}
save(D/'package.json',p);shutil.copyfile(D/'package.json',E/'prepared-package.json')
shutil.copyfile(binary,E/'pose_shared_timing.arm64')
(E/'verification-source').mkdir()
for name in ('shared_output_gate.hpp','selftest.cpp','replay.cpp'):shutil.copyfile(MOD/name,E/'verification-source'/name)
with tarfile.open(E/'source.tar.gz','x:gz') as t:
    for f in sorted(S.rglob('*')):
        if f.is_file():t.add(f,arcname=f.relative_to(S).as_posix(),recursive=False)

revision=[]
for v in load(E/'revision-before.json'):
    path=Path(v['Path']);revision.append(dict(path=str(path),before_sha256=v['Hash'].lower(),after_sha256=sha(path),
        changed=sha(path)!=v['Hash'].lower()))
save(E/'documentation-revision.json',dict(reason='Explicit score>0.2 position-gate scope and user stage acceptance; preserve all original failures',
    files=revision,historical_evidence_only_entries_verified=len(evidence_entries),original_delivery_entries_verified=len(first)))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()
save(E/'workspace-transition-review.json',dict(observation='Temporary file absence during branch checkout to master and fast-forward merge',
    verified_head=head,reflog=subprocess.check_output(['git','reflog','-3','--date=iso'],cwd=R,text=True).splitlines(),
    ARM_source_matches_current_header=True,previous_evidence_unchanged=True,agent_reset_or_history_rewrite=False))

for md in [E/'REPORT.md',R/'ADR/ADR_48.md',MOD/'README.md']:
    missing=[target for target in re.findall(r'\]\(([^)]+)\)',md.read_text(encoding='utf-8'))
             if '://' not in target and not (md.parent/target.split('#')[0]).exists()]
    assert not missing,(md,missing)
diff=subprocess.run(['git','diff','--check'],cwd=R,capture_output=True)
(E/'git-diff-check.txt').write_bytes(diff.stdout+diff.stderr);assert diff.returncode==0
files={}
for base in [E,MOD]:
    for path in sorted(base.rglob('*')):
        if path.is_file() and path.name not in ('delivery-files.json','completion-review.json'):
            files[str(path)]=dict(bytes=path.stat().st_size,sha256=sha(path))
save(E/'delivery-files.json',files)
save(E/'completion-review.json',dict(status='confidence_scoped_gate_implemented_three_saved_frames_pass',
    policy='shared-fp16-score-gt02-joint-3mm-v2',user_stage_acceptance_recorded=True,
    boundary_rejection_checks=21,ARM_build_exit=0,offline_CPP_replay_exit=[0,0,0],
    saved_frames_pass=3,max_checked_joint_delta_mm=a['max_checked_joint_delta_mm'],
    background_diagnostics_retained=True,all_candidates_finite_checks_retained=True,
    new_board_inferences=0,new_board_deployment=False,old_board_exit_preserved=1,
    physical_bias_or_training_drift_proven=False,model_RAW_or_formal_demo_changed=False,
    old_DATA_investigation_resumed=False,FPAI_final_status='exited',
    source_archive_sha256=sha(E/'source.tar.gz'),ARM_binary_sha256=sha(binary),
    prepared_package_sha256=sha(D/'package.json'),report=str(E/'REPORT.md'),
    report_sha256=sha(E/'REPORT.md'),delivery_files=len(files),delivery_manifest_sha256=sha(E/'delivery-files.json')))
print(json.dumps(dict(status='completed',saved_frames_pass=3,new_board_inferences=0,files=len(files)),ensure_ascii=False))
