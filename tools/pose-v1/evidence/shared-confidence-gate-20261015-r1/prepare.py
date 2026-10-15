"""Prepare the confidence-scoped gate in a fresh source/delivery, preserving old runs."""
import hashlib,json,shutil
from pathlib import Path
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
PREV=R/'tools/pose-v1/evidence/shared-gate-policy-20261015-r1'
OLD=R/'.local/shared-gate-source-20261015-r1';OLD_D=R/'.local/shared-gate-delivery-20261015-r1'
S=R/'.local/shared-confidence-source-20261015-r1';D=R/'.local/shared-confidence-delivery-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not S.exists() and not D.exists()
for n,h in json.loads((PREV/'source-manifest.json').read_text(encoding='utf-8'))['files'].items():assert sha(OLD/n)==h,n
shutil.copytree(OLD,S,ignore=shutil.ignore_patterns('source-manifest.json'))
shutil.copytree(OLD_D,D,ignore=shutil.ignore_patterns('source-manifest.json','package.json','pose_shared_timing','policy.json'))
shutil.copyfile(R/'tools/pose-v1/shared-output-gate/shared_output_gate.hpp',S/'shared_output_gate.hpp')
p=S/'main.cpp';s=p.read_text(encoding='utf-8')
assert s.count('actual.scores, c.scores, actual.poses, c.poses, 3.0);')==1
s=s.replace('actual.scores, c.scores, actual.poses, c.poses, 3.0);',
            'actual.scores, c.scores, actual.poses, c.poses, 3.0, 0.2f);')
s=s.replace('shared-fp16-joint-3mm-v1','shared-fp16-score-gt02-joint-3mm-v2')
s=s.replace('Output exceeds approved shared 3mm gate or score/finite check failed; stop without retry',
    'Confident pose exceeds approved 3mm gate or complete score/finite check failed; stop without retry')
s=s.replace('bounded_numeric_run_completed','confidence_scoped_numeric_run_completed')
s=s.replace('全部分数逐位、每个候选关节欧氏差<=3mm；超限停止。',
            '全部分数逐位、仅score>0.2候选关节欧氏差<=3mm；非有限值/超限停止。')
old='''                        << ",\\\"max_joint_delta_mm\\\":" << comparison.max_joint_delta_mm'''
new=old+'''
                        << ",\\\"checked_candidates\\\":" << comparison.checked_candidates
                        << ",\\\"excluded_candidates\\\":" << comparison.excluded_candidates
                        << ",\\\"position_gate_applicable\\\":" << (comparison.checked_candidates ? "true" : "false")
                        << ",\\\"max_checked_joint_delta_mm\\\":" << comparison.max_checked_joint_delta_mm
                        << ",\\\"max_excluded_joint_delta_mm\\\":" << comparison.max_excluded_joint_delta_mm
                        << ",\\\"excluded_over_limit_joints\\\":" << comparison.excluded_over_limit_joints'''
assert s.count(old)==1;s=s.replace(old,new);p.write_text(s,encoding='utf-8',newline='\n')
policy=json.loads((PREV/'policy.json').read_text(encoding='utf-8'))
policy.update(id='shared-fp16-score-gt02-joint-3mm-v2',
    user_instruction='仅对score>0.2的候选进行3mm关节误差检查，低分背景候选不参与位置硬门限比较；用户认为当前阶段基本通过',
    scope='Same fixed shared FP16 graph and same-slot joint comparison, restricted to reference score>FP32(0.2)',
    minimum_checked_score=0.2,score_operator='strictly greater than',score_threshold_storage='FP32 literal 0.2f',
    zero_selected='position gate inapplicable; finite values and complete score identity still checked',
    background='all raw values and errors retained; no position hard limit; finite checks retained',
    cause='FP16 step-sized differences observed; exact source and low-score training-drift hypothesis unproven',
    historical_failure_rewritten=False)
save(E/'policy.json',policy);save(D/'policy.json',policy)
manifest=dict(status='confidence_scoped_source_prepared_not_board_run',source_origin=str(OLD),policy=policy,
    files={str(p.relative_to(S)):sha(p) for p in sorted(S.rglob('*')) if p.is_file()})
save(S/'source-manifest.json',manifest);save(D/'source-manifest.json',manifest);save(E/'source-manifest.json',manifest)
print(json.dumps(dict(source=str(S),delivery=str(D),policy=policy['id'])))
