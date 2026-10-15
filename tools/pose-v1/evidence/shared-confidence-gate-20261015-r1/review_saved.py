"""Re-evaluate frozen real board arrays using the new C++ gate and an independent mask."""
from pathlib import Path
import hashlib,json,subprocess
import numpy as np
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
P=R/'tools/pose-v1/evidence/shared-gate-policy-20261015-r1';RUN=P/'returned/run-wall'
F=R/'.local/shared-confidence-delivery-20261015-r1/fixtures'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
for n,h in load(RUN/'evidence-files.json').items():assert sha(RUN/n)==h,n
old=load(P/'analysis.json');assert old['status']=='3mm_policy_implemented_third_frame_rejected'
policy=load(E/'policy.json')
for ext,k in [('json','graph_json_sha256'),('raw','graph_raw_sha256')]:
    assert sha(R/'model/piw24_shared-20261015-r1'/('piw24_shared_ZG.'+ext))==policy[k]
replay=R/'.local/shared-confidence-replay-20261015.exe'
frames=[]
for i,case in enumerate(['S11_01_308','S11_01_309','S11_01_310']):
    actual=RUN/'results'/('frame-'+str(i));stem=F/case
    cmd=[str(replay),str(actual/'scores.f32'),str(stem)+'.scores.f32',str(actual/'poses.f32'),str(stem)+'.poses.f32']
    p=subprocess.run(cmd,capture_output=True,timeout=10)
    (E/(case+'.cpp.stdout.json')).write_bytes(p.stdout);(E/(case+'.cpp.stderr.txt')).write_bytes(p.stderr)
    assert p.returncode==0 and not p.stderr,(case,p.returncode,p.stderr)
    cpp=json.loads(p.stdout)
    a=np.fromfile(actual/'scores.f32',dtype='<f4');b=np.fromfile(str(stem)+'.scores.f32',dtype='<f4')
    ap=np.fromfile(actual/'poses.f32',dtype='<f4').reshape(100,14,3)
    bp=np.fromfile(str(stem)+'.poses.f32',dtype='<f4').reshape(100,14,3)
    actual_input=(actual/'input.f32').read_bytes();reference_input=Path(str(stem)+'.input.f32').read_bytes()
    assert len(a)==len(b)==100 and len(actual_input)==10800*4
    assert actual_input==reference_input and a.tobytes()==b.tobytes()
    assert all(np.isfinite(v).all() for v in (a,b,ap,bp))
    checked=b>np.float32(.2);delta=(ap.astype('f8')-bp.astype('f8'))*1000
    norm=np.linalg.norm(delta,axis=-1)
    max_checked=float(norm[checked].max()) if checked.any() else None
    max_excluded=float(norm[~checked].max()) if (~checked).any() else None
    assert int(checked.sum())==cpp['checked_candidates']
    assert abs((max_checked or 0)-cpp['max_checked_joint_delta_mm'])<1e-12
    assert abs((max_excluded or 0)-cpp['max_excluded_joint_delta_mm'])<1e-12
    changed=ap.view('u4')!=bp.view('u4')
    outliers=[dict(candidate=int(c),joint=int(j),score=float(b[c]),delta_mm=delta[c,j].tolist(),
                   joint_delta_mm=float(norm[c,j]),position_checked=bool(checked[c]))
              for c,j in np.argwhere(norm>3)]
    assert all(not v['position_checked'] for v in outliers)
    frames.append(dict(case=case,cpp_exit=p.returncode,cpp=cpp,
        checked_candidate_ids=np.flatnonzero(checked).tolist(),checked_scores=b[checked].astype('f8').tolist(),
        max_checked_joint_delta_mm=max_checked,max_excluded_joint_delta_mm=max_excluded,
        changed_checked_coordinates=int(changed[checked].sum()),changed_excluded_coordinates=int(changed[~checked].sum()),
        all_candidate_over_limit_diagnostics=outliers,position_gate_applicable=bool(checked.any()),
        actual_files={n:sha(actual/(n+'.f32')) for n in ('input','scores','poses')},
        saved_original_timing_ms=old['frames'][i]['timing_ms']))
assert all(f['cpp']['accepted'] for f in frames)
report=dict(status='three_saved_frames_pass_confidence_scoped_gate_offline',policy=policy,
    verification_platform='Windows CPU; actual C++ gate replay plus independent NumPy calculation',
    new_board_inferences=0,original_board_run_exit=1,original_failures_preserved=True,
    frames=frames,accepted_under_new_policy=3,rejected_under_new_policy=0,
    total_checked_candidates=sum(f['cpp']['checked_candidates'] for f in frames),
    total_excluded_candidates=sum(f['cpp']['excluded_candidates'] for f in frames),
    max_checked_joint_delta_mm=max(f['max_checked_joint_delta_mm'] or 0 for f in frames),
    max_all_candidate_joint_delta_mm=max(f['cpp']['max_joint_delta_mm'] for f in frames),
    changed_checked_coordinates=sum(f['changed_checked_coordinates'] for f in frames),
    changed_excluded_coordinates=sum(f['changed_excluded_coordinates'] for f in frames),
    MPJPE_reused_unchanged=old['mean_three_frame_MPJPE_mm'],
    saved_board_Engine_ms_mean=old['mean_all_three_measured_frames_ms']['process_ms'],
    user_stage_acceptance='User regards current shared-refinement stage as basically passed; recorded within current three-frame scope',
    physical_bias_and_training_drift_proven=False,
    limits=['Offline policy re-evaluation, not a new successful board process exit',
            'Only one confident candidate per saved frame; no full-dataset confidence gate or long-run acceptance',
            'All background bytes and errors retained; all finite/score checks remain'])
save(E/'analysis.json',report)
print(json.dumps(dict(status=report['status'],max_checked_joint_delta_mm=report['max_checked_joint_delta_mm'],
    cases=[dict(case=f['case'],checked_ids=f['checked_candidate_ids'],max_checked_mm=f['max_checked_joint_delta_mm'],
                changed_checked=f['changed_checked_coordinates'],changed_background=f['changed_excluded_coordinates']) for f in frames]),indent=2))
