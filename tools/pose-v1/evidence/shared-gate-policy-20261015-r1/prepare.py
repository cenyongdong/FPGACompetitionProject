"""Prepare a new bounded validation after the user's explicit 3 mm decision."""
import hashlib,json,shutil
from pathlib import Path
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
PREV=R/'tools/pose-v1/evidence/shared-graph-board-20261015-r1'
OLD=R/'.local/shared-source-20261015-r1';OLD_D=R/'.local/shared-delivery-20261015-r1'
S=R/'.local/shared-gate-source-20261015-r1';D=R/'.local/shared-gate-delivery-20261015-r1'
T=R/'.local/shared-gate-transport-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
assert not S.exists() and not D.exists() and not T.exists()
for n,h in json.loads((PREV/'source-manifest.json').read_text())['files'].items():assert sha(OLD/n)==h
shutil.copytree(OLD,S,ignore=shutil.ignore_patterns('source-manifest.json'))
shutil.copytree(OLD_D,D,ignore=shutil.ignore_patterns('source-manifest.json','package.json','pose_shared_timing'))
shutil.copyfile(R/'tools/pose-v1/shared-output-gate/shared_output_gate.hpp',S/'shared_output_gate.hpp')
p=S/'main.cpp';s=p.read_text(encoding='utf-8')
s=s.replace('// 独立有限诊断入口：保存完整实际值后逐位比较，异常永久停止唯一Engine。',
            '// 独立有限诊断入口：保存完整实际值后执行用户批准的3mm门检，异常停止。')
s=s.replace('#include "application_core.hpp"','#include "application_core.hpp"\n#include "shared_output_gate.hpp"')
old='''                const bool matched = std::memcmp(actual.scores.data(), c.scores.data(), sizeof(c.scores)) == 0 &&
                                     std::memcmp(actual.poses.data(), c.poses.data(), sizeof(c.poses)) == 0;'''
new='''                const auto comparison = pose::shared_output_gate::compare(
                    actual.scores, c.scores, actual.poses, c.poses, 3.0);
                const bool matched = comparison.accepted;'''
assert s.count(old)==1;s=s.replace(old,new)
old='''                        << ",\\\"process_ms\\\":" << actual.process_ms'''
new='''                        << ",\\\"gate_policy\\\":\\\"shared-fp16-joint-3mm-v1\\\""
                        << ",\\\"scores_bitwise_equal\\\":" << (comparison.scores_bitwise_equal ? "true" : "false")
                        << ",\\\"poses_bitwise_equal\\\":" << (comparison.poses_bitwise_equal ? "true" : "false")
                        << ",\\\"finite\\\":" << (comparison.finite ? "true" : "false")
                        << ",\\\"changed_pose_values\\\":" << comparison.changed_pose_values
                        << ",\\\"max_coordinate_delta_mm\\\":" << comparison.max_coordinate_delta_mm
                        << ",\\\"max_joint_delta_mm\\\":" << comparison.max_joint_delta_mm
                        << ",\\\"process_ms\\\":" << actual.process_ms'''
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('Complete output differs; stop without retry','Output exceeds approved shared 3mm gate or score/finite check failed; stop without retry')
s=s.replace('finite_numeric_run_completed','bounded_numeric_run_completed')
s=s.replace('// 先保存完整实际输出，再比较；失配停止，晚源不修补结果。',
            '// 先保存完整实际输出；全部分数逐位、每个候选关节欧氏差<=3mm；超限停止。')
p.write_text(s,encoding='utf-8',newline='\n')
policy=dict(id='shared-fp16-joint-3mm-v1',user_instruction='最大误差可以定在3mm以内',
    scope='Only shared-refinement FP16 candidate, exact pinned graph/RAW; same-slot all100 candidates x14 joints',
    max_joint_euclidean_delta_mm=3.0,inclusive=True,model_units_to_mm=1000.0,
    scores='all100 bitwise equal',input='all10800 bitwise equal',
    finite='all inputs/outputs/references finite; nonfinite stops',
    MPJPE='Report measured changes; no new hard MPJPE threshold was specified by user',
    graph_json_sha256=sha(D/'models/piw24_shared_ZG.json'),
    graph_raw_sha256=sha(D/'models/piw24_shared_ZG.raw'),
    no_candidate_rematching=True,no_output_repair=True,save_before_compare=True,
    SDK_index_identity_timeout_stops_unchanged=True,
    cause='Unknown; physical bias is user hypothesis, not experimentally established',
    historical_failure_rewritten=False,original_formal_core_gate_changed=False)
save(E/'policy.json',policy);save(D/'policy.json',policy)
manifest=dict(status='new_source_with_approved_bounded_gate_not_yet_executed',source_origin=str(OLD),
    policy=policy,files={str(p.relative_to(S)):sha(p) for p in sorted(S.rglob('*')) if p.is_file()})
save(S/'source-manifest.json',manifest);save(D/'source-manifest.json',manifest);save(E/'source-manifest.json',manifest)
T.mkdir();text=(R/'.local/shared-transport-20261015-r1/secure_transport.py').read_text(encoding='utf-8')
(T/'secure_transport.py').write_text(text.replace('/tmp/wifi-pose-shared-20261015-r1/','/tmp/wifi-pose-shared-gate-20261015-r1/'),encoding='utf-8')
for name in ('package.py','execute.py'):
    text=(PREV/name).read_text(encoding='utf-8').replace('shared-graph-board-20261015-r1','shared-gate-policy-20261015-r1')
    text=text.replace('shared-source-20261015-r1','shared-gate-source-20261015-r1').replace('shared-delivery-20261015-r1','shared-gate-delivery-20261015-r1')
    text=text.replace('shared-transport-20261015-r1','shared-gate-transport-20261015-r1').replace('/tmp/wifi-pose-shared-20261015-r1','/tmp/wifi-pose-shared-gate-20261015-r1')
    text=text.replace('All100 scores and all4200 coordinates bitwise vs saved original board outputs; stop on mismatch',
        'All100 scores bitwise; all100x14 same-slot joint Euclidean deltas <=3mm; stop on any violation')
    text=text.replace('output byte discrepancy','score byte discrepancy or joint Euclidean delta >3mm')
    text=text.replace('04-install-r2','04-install')
    text=text.replace("reference_gate_relaxed=False", "reference_gate_relaxed=True, policy='shared-fp16-joint-3mm-v1'")
    (E/name).write_text(text,encoding='utf-8',newline='\n')
print(json.dumps(dict(source=str(S),delivery=str(D),policy=policy['id'])))
