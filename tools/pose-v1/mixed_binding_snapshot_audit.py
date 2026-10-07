"""Offline audit of the pinned r2 snapshots; never creates a Session or acceptance."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import runpy

HOST = 'icraft::xrt::HostBackendNode'
ZG = 'icraft::xrt::zg330::ZG330BackendNode'
HOST_IDS = {0, 188, 192, 437, 442, 582, 649, 672}
PARTS = ('all-bindings', 'views', 'backends', 'zg-hardop-map', 'zg-sync-map')


def require(test, reason):
    if not test:
        raise ValueError(reason)


def indexed(rows, key):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), 'Duplicate ' + key)
    return result


def audit(snapshots):
    before, after = snapshots['after-create'], snapshots['after-apply']
    original = [v for v in before['views'] if v['owner'] == 'original_graph']
    ids = indexed(original, 'op_id')
    hard = {i for i, v in ids.items() if v['is_hardop']}
    nonhard = set(ids) - hard
    require(len(ids) == 1181 and len(hard) == 1173 and nonhard == HOST_IDS, 'Original graph baseline differs')
    require(all(ids[i]['operator'] == 'icraft::xir::HardOpNode' for i in hard), 'HardOp runtime type differs')
    for phase in (before, after):
        require(phase['backends'] == [{'backend_index': 0, 'backend': ZG},
                                     {'backend_index': 1, 'backend': HOST}], 'Backend inventory differs')
        for owner, wanted in [('original_graph', set(ids)), ('session_view', set(ids)),
                              ('backend_0', hard), ('backend_1', nonhard)]:
            view = indexed([v for v in phase['views'] if v['owner'] == owner], 'op_id')
            require(set(view) == wanted, 'View membership differs: ' + owner)
            require(all(view[i]['operator'] == ids[i]['operator'] and
                        view[i]['is_hardop'] == ids[i]['is_hardop'] for i in wanted), 'View types differ')
        require({v['owner'] for v in phase['views']} ==
                {'original_graph', 'session_view', 'backend_0', 'backend_1'}, 'Unknown view owner')
    initial = indexed(before['all-bindings'], 'binding_key')
    require(set(initial) == set(ids), 'Create binding coverage differs')
    require(all(initial[i]['backend'] == ZG for i in hard) and
            all(initial[i]['backend'] == HOST for i in nonhard), 'Create backend assignment differs')
    require(not before['zg-hardop-map'] and not before['zg-sync-map'], 'Unexpected create maps')
    final = indexed(after['all-bindings'], 'binding_key')
    require(all(i in final and final[i]['backend'] == HOST for i in nonhard), 'Host binding changed')
    groups = {i for i, v in final.items() if v['backend'] == ZG}
    require(len(groups) == 7 and set(final) == groups | nonhard and not groups & set(ids), 'Effective binding baseline differs')
    maps = indexed(after['zg-hardop-map'], 'op_id')
    sync = indexed(after['zg-sync-map'], 'map_key')
    require(set(maps) == set(sync) == hard | groups, 'ZG map key coverage differs')
    for i, v in maps.items():
        require(v['backend_index'] == 0 and v['entry_defined'] and v['net_hardop_id'] == i, 'ZG map identity differs')
        require(sync[i]['backend_index'] == 0 and
                (sync[i]['sync_index'], sync[i]['layer_count']) == (v['sync_index'], v['layer_count']), 'ZG sync map mismatch')
        # Original logical entries can have zero deployed layers (428 in this snapshot).
        # Only a bound effective group requires a positive deployed layer count.
        require(v['sync_index'] >= 0 and v['layer_count'] >= 0 and
                (i not in groups or v['layer_count'] > 0), 'Invalid sync metadata')
        if i in hard:
            require(not v['merge_from'], 'Original entry unexpectedly merged')
    mapping, summary = {}, []
    for group in sorted(groups):
        members = maps[group]['merge_from']
        require(members and len(set(members)) == len(members), 'Empty/duplicate group members')
        for i in members:
            require(i in hard and i not in mapping, 'Extra or multiply covered original HardOp')
            mapping[i] = group
        summary.append(dict(effective_op_id=group, original_hardop_count=len(members),
                            sync_index=maps[group]['sync_index'], layer_count=maps[group]['layer_count']))
    require(set(mapping) == hard, 'Uncovered original HardOp')
    return mapping, summary


def rejection_checks(snapshots):
    tests = []
    def test(name, mutate):
        changed = copy.deepcopy(snapshots)
        mutate(changed)
        try:
            audit(changed)
        except (ValueError, KeyError) as error:
            tests.append({'case': name, 'rejected': True, 'reason': str(error)})
        else:
            raise AssertionError('Bad snapshot accepted: ' + name)
    def group(s):
        return next(v for v in s['after-apply']['zg-hardop-map'] if v['merge_from'])
    test('missing_original_member', lambda s: group(s)['merge_from'].pop())
    test('duplicate_original_member', lambda s: group(s)['merge_from'].append(group(s)['merge_from'][0]))
    test('host_as_hardop_member', lambda s: group(s)['merge_from'].append(188))
    test('missing_effective_binding', lambda s: s['after-apply']['all-bindings'].pop())
    test('wrong_effective_backend', lambda s: next(v for v in s['after-apply']['all-bindings'] if v['backend'] == ZG).update(backend=HOST))
    test('wrong_group_map_identity', lambda s: group(s).update(net_hardop_id=-1))
    test('sync_metadata_mismatch', lambda s: s['after-apply']['zg-sync-map'][0].update(layer_count=-1))
    test('host_binding_changed', lambda s: next(v for v in s['after-apply']['all-bindings'] if v['binding_key'] == 442).update(backend=ZG))
    test('create_hardop_on_host', lambda s: next(v for v in s['after-create']['all-bindings'] if v['backend'] == ZG).update(backend=HOST))
    return tests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('results', 'package', 'build', 'previous', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    a = parser.parse_args()
    require(not a.output.exists(), 'Preserve prior audit output')
    g = runpy.run_path(str(Path(__file__).with_name('mixed_validation_gate.py')))
    returned, packaged = g['verify'](a.results), g['verify'](a.package)
    manifest, build = g['load'](a.package / 'manifest.json'), g['load'](a.build / 'build-result.json')
    g['sdk'](g['load'](a.results / 'sdk-audit.json'), manifest)
    require(g['sha'](a.results / 'pose_mixed_check') == g['sha'](a.build / 'pose_mixed_check.arm64') == build['binary_sha256'], 'Binary identity differs')
    require(g['sha'](a.package / 'manifest.json') == build['package_manifest_sha256'], 'Package identity differs')
    previous = g['load'](a.results / 'previous-acceptance.json')
    require(previous == g['load'](a.previous) and previous['stage'] == 'memory-check' and
            previous['status'] == 'stage_engineering_review_passed' and
            previous['binary_sha256'] == build['binary_sha256'] and
            previous['package_manifest_sha256'] == build['package_manifest_sha256'], 'Previous memory approval differs')
    identity = g['load'](a.results / 'run-identity.json')
    require(identity['stage'] == 'apply-check' and identity['binary_sha256'] == build['binary_sha256'] and
            identity['package_manifest_sha256'] == build['package_manifest_sha256'], 'Run identity differs')
    out = a.results / 'results'
    g['registry'](out / 'registry.jsonl')
    config = g['load'](out / 'run-config.json')
    require(config['mode'] == 'apply-check' and config['device_init_allowed'], 'Run scope differs')
    require((a.results / 'exit.txt').read_text().strip() == '1', 'Unexpected exit; review separately')
    error = 'STOP: Original op lacks traceable backend binding (including any fusion): 8622'
    require((a.results / 'run.stderr.log').read_text().strip() == error, 'Unexpected failure')
    stages = [v['stage'] for v in g['lines'](out / 'stages.jsonl')]
    require(stages == ['started', 'real_parameters_validated', 'registered_before_session',
                       'opening_device_not_readonly', 'session_applied', 'failed_stop_no_retry'], 'Unexpected stages')
    require((out / 'bridge.jsonl').stat().st_size == 0 and not (out / 'results.jsonl').exists(), 'Unexpected forward artifacts')
    require((a.results / 'dmesg.before.log').read_bytes() == (a.results / 'dmesg.after.log').read_bytes(), 'Kernel log changed; review separately')
    require('not found' not in (a.results / 'ldd.txt').read_text(), 'Unresolved dependency')
    version = g['load'](out / 'device-version.json')
    require(version['url'] == 'axi://zg330aiu?npu=0x40000000&dma=0x80000000' and
            version['versions'] == {'device': '25122301', 'icore': 'FMSHZGV3TECH-AID - 24160628'}, 'Device identity differs')
    snapshots = {phase: {part: g['lines'](out / f'{phase}.{part}.jsonl') for part in PARTS}
                 for phase in ('after-create', 'after-apply')}
    mapping, groups = audit(snapshots)
    tests = rejection_checks(snapshots)
    a.output.mkdir()
    trace = a.output / 'original-to-effective.jsonl'
    trace.write_text(''.join(json.dumps(dict(op_id=i, effective_op_id=mapping[i], backend=ZG)) + '\n'
                             for i in sorted(mapping)), encoding='utf-8')
    report = dict(status='binding_snapshots_audited_not_apply_accepted', returned_files_verified=returned,
                  package_files_verified=packaged, binary_sha256=build['binary_sha256'],
                  snapshot_counts={phase: {part: len(v) for part, v in parts.items()} for phase, parts in snapshots.items()},
                  original_hardops_covered=len(mapping), missing=0, duplicate_coverage=0, extra_members=0,
                  host_computation_nodes_preserved=[188, 192, 437, 442, 582, 649], groups=groups,
                  original_zero_layer_entries=sum(v['layer_count'] == 0 for v in snapshots['after-apply']['zg-hardop-map'] if not v['merge_from']),
                  failing_original=8622, actual_effective_binding=mapping[8622],
                  rejection_checks=tests, mapping_sha256=hashlib.sha256(trace.read_bytes()).hexdigest(),
                  device_version=version, dmesg_unchanged=True, model_forward_executed=False,
                  apply_acceptance_generated=False, numerical_accepted=False,
                  agent_activity='Offline file analysis only; no board/SDK calls.',
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (a.output / 'review.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Snapshot audit passed: 1173 original HardOps covered exactly once by 7 bound ZG groups; 9 malformed snapshots rejected. No apply acceptance.')


if __name__ == '__main__':
    main()
