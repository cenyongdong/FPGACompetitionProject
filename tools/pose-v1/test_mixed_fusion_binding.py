"""Replay fusion validation with reviewed r2 metadata; no compiler/SDK/device calls."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import runpy
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    a = parser.parse_args()
    assert not a.output.exists(), 'Preserve earlier replay'
    root = Path(__file__).resolve().parents[2]
    gate = runpy.run_path(str(root / 'tools/pose-v1/mixed_validation_gate.py'))
    helper = runpy.run_path(str(root / 'tools/pose-v1/mixed_binding_snapshot_audit.py'))
    baseline = gate['load'](root / 'tools/pose-v1/mixed-fusion-baseline.json')
    snapshots = {phase: {part: gate['lines'](a.source / f'{phase}.{part}.jsonl') for part in helper['PARTS']}
                 for phase in ('after-create', 'after-apply')}
    mapping, groups = helper['audit'](snapshots)
    tests = helper['rejection_checks'](snapshots)
    # Confirm the C++ baseline contains exactly the same original member sets and sync pairs.
    header = (root / 'software/pose_v1/include/mixed_fusion_baseline.hpp').read_text()
    section = header.split('members={', 1)[1].split('inline const', 1)[0]
    cpp = {int(k): [int(x) for x in re.findall(r'\d+', values)]
           for k, values in re.findall(r'\{(\d+),\s*\{(.*?)\}\}', section, re.S)}
    assert cpp == {g['effective_op_id']: g['members'] for g in baseline['groups']}
    pairs = {int(k): (int(i), int(n)) for k, i, n in
             re.findall(r'\{(\d+),\{(\d+),(\d+)\}\}', header.split('sync={', 1)[1])}
    assert pairs == {g['effective_op_id']: (g['sync_index'], g['layer_count']) for g in baseline['groups']}
    a.output.mkdir(parents=True)
    replay = a.output / 'synthetic-formal-trace-replay'
    replay.mkdir()
    for phase in snapshots:
        for part in helper['PARTS']:
            shutil.copyfile(a.source / f'{phase}.{part}.jsonl', replay / f'{phase}.{part}.jsonl')
    original = [v for v in snapshots['after-create']['views'] if v['owner'] == 'original_graph']
    bound = [dict(op_id=v['op_id'], operator=v['operator'], is_hardop=v['is_hardop'],
                  effective_op_id=mapping[v['op_id']] if v['is_hardop'] else v['op_id'],
                  binding_kind='zg_merge_from' if v['is_hardop'] else 'host_direct',
                  backend=helper['ZG'] if v['is_hardop'] else helper['HOST']) for v in original]
    binding_path = replay / 'bindings.jsonl'
    def write_bound(rows):
        binding_path.write_text(''.join(json.dumps(v) + '\n' for v in rows), encoding='utf-8')
    write_bound(bound)
    summary_path = replay / 'binding-summary.json'
    summary = dict(original_ops=1181, original_hardops=1173, direct_host_ops=8,
                   effective_zg_groups=7, coverage_complete=True)
    summary_path.write_text(json.dumps(summary) + '\n', encoding='utf-8')
    assert gate['fusion_binding_review'](replay, baseline) == groups
    first_hard = next(i for i, row in enumerate(bound) if row['is_hardop'])
    def reject_trace(name, change):
        changed = copy.deepcopy(bound)
        change(changed)
        write_bound(changed)
        try:
            gate['fusion_binding_review'](replay, baseline)
        except (ValueError, KeyError) as error:
            tests.append(dict(case=name, rejected=True, reason=str(error)))
        else:
            raise AssertionError('Invalid trace accepted: ' + name)
        finally:
            write_bound(bound)
    reject_trace('missing_trace_row', lambda v: v.pop())
    reject_trace('duplicate_original_trace', lambda v: v.__setitem__(first_hard, v[0]))
    reject_trace('forged_effective_op_id', lambda v: v[first_hard].update(effective_op_id=-1))
    reject_trace('HardOp_false_flag', lambda v: v[first_hard].update(is_hardop=False))
    reject_trace('wrong_HardOp_runtime_type', lambda v: v[first_hard].update(operator='icraft::xir::HardOp'))
    reject_trace('wrong_trace_backend', lambda v: v[first_hard].update(backend=helper['HOST']))
    reject_trace('wrong_binding_kind', lambda v: v[first_hard].update(binding_kind='host_direct'))
    changed = copy.deepcopy(baseline)
    changed['groups'][0]['members'].pop()
    try:
        gate['fusion_binding_review'](replay, changed)
    except ValueError as error:
        tests.append(dict(case='pinned_group_members_changed', rejected=True, reason=str(error)))
    else:
        raise AssertionError('Changed baseline accepted')
    summary_path.write_text(json.dumps(dict(summary, original_hardops=7)), encoding='utf-8')
    try:
        gate['fusion_binding_review'](replay, baseline)
    except ValueError as error:
        tests.append(dict(case='group_count_as_original_count', rejected=True, reason=str(error)))
    else:
        raise AssertionError('False coverage count accepted')
    finally:
        summary_path.write_text(json.dumps(summary) + '\n', encoding='utf-8')
    assert gate['fusion_binding_review'](replay, baseline) == groups
    report = dict(status='offline_fusion_replay_passed_not_ARM_runtime', original_hardops=1173,
                  logical_trace_rows=1181, effective_groups=7, malformed_cases_rejected=len(tests),
                  tests=tests, cpp_baseline_matches_json=True, original_r2_results_modified=False,
                  trace_origin='Synthetic expected r3 trace constructed from real reviewed r2 snapshots; not emitted by ARM program.',
                  compiler_executed=False, board_accessed=False, model_forward_executed=False,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.output / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'Offline fusion replay passed: 1181 logical rows, 1173 HardOps, 7 groups; {len(tests)} malformed cases rejected. No ARM execution.')


if __name__ == '__main__':
    main()
