"""Independent post-place read-only audit and exclusive evidence projection.

No EDA, SDK, remote or board entry. The original aa175 wrapper remains failed.
Only an actual completed phys_opt tool session with its one known postcheck
error is eligible. Inspect never creates files; audit/publish are separate.
"""
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import re
import shutil
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SCRIPT = Path(__file__).resolve()
START_BYTES = SCRIPT.read_bytes()
START_SHA = hashlib.sha256(START_BYTES).hexdigest()
SCRIPTS = SCRIPT.parent
E = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r7'
W = ROOT / '.local/hdmi-live-20261017-r7'
REF = W / 'reference'
PHASE = E / 'read-v3r7-place'
NATIVE = REF / 'fpai_demo_vivado.runs/impl_read_v3r7'
AUDIT = E / 'place-completion-review-r1'
DRIVER = SCRIPTS / 'continue_hdmi_reader_idle_candidate.py'
DRIVER_SHA = 'aa175d681abc632625df8e7ec7a74cf332fa59a1dd3e0ab39066074c1696f2a6'
CONTRACT = SCRIPTS / 'ai_read_r7_contract.py'
CONTRACT_SHA = 'fa28b01f12baf593788d554fae942564ff69753caf1310cd034a48d08178fdc8'
OWNER_SHA = '3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672'
PROFILE_SHA = '4390afb69c4952ad4699f24a1c9aa00b21f326f466fa916d6f86ea18a4311357'
ERROR = 'ValueError: Original implementation command missing/duplicated: route_design -directive NoTimingRelaxation'
SENTINEL = 'HDMI_READER_R7_NEW_PHYSOPT_CHECKPOINT_COMPLETE_NOT_ROUTED'
CANONICAL = ('actual-native.tcl', 'native-script.tcl', 'native-source-identity.json',
             'checkpoint-identity.json', 'phase-artifacts.json', 'projection-provenance.json', 'phase-review.json')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def raw_json(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def same(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(',', ':'), allow_nan=False)


def source_guard():
    need(SCRIPT.read_bytes() == START_BYTES and sha(DRIVER) == DRIVER_SHA
         and sha(CONTRACT) == CONTRACT_SHA, 'Frozen audit/aa175/fa28 source changed')


def module(path, expected, name):
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'Frozen source differs: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


def file_record(path, mtime=False):
    path = Path(path)
    need(path.is_file() and not path.is_symlink(), 'Missing/nonordinary evidence: ' + str(path))
    result = {'bytes': path.stat().st_size, 'SHA256': sha(path)}
    if mtime:
        result['mtime_ns'] = path.stat().st_mtime_ns
    return result


def checkpoint(path):
    result = file_record(path)
    need(result['bytes'] > 0, 'Empty actual checkpoint')
    return {'path': str(path), **result}


def inventory(directory):
    result = {}
    need(directory.is_dir() and not directory.is_symlink(), 'Evidence directory absent/nonordinary')
    for path in sorted(directory.rglob('*')):
        need(not path.is_symlink() and path.resolve().is_relative_to(directory.resolve()), 'Evidence path escaped')
        if path.is_file():
            result[path.relative_to(directory).as_posix()] = file_record(path, True)
    return result


def save_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw)


def wrapper_outcome(receipt):
    """The root preserves the original merged write_stdin result, never split streams."""
    need(receipt.get('schema') == 'r7-place-wrapper-outcome-v1'
         and receipt.get('completed') is True and type(receipt.get('session_id')) is int
         and receipt['session_id'] == 2330 and isinstance(receipt.get('source_tool'), str)
         and 'write_stdin' in receipt['source_tool'] and isinstance(receipt.get('command'), str)
         and 'continue_hdmi_reader_idle_candidate.py' in receipt['command']
         and re.search(r'\bplace\b', receipt['command']) is not None,
         'Actual completed root wrapper outcome missing/incorrect')
    result = receipt.get('tool_result', {})
    text = result.get('output', '')
    need(type(result.get('exit_code')) is int and result['exit_code'] == 1
         and isinstance(text, str) and text.count('Traceback (most recent call last):') == 1
         and [line for line in text.splitlines() if line.startswith(('ValueError:', 'RuntimeError:', 'AssertionError:'))] == [ERROR]
         and text.rstrip().endswith(ERROR) and 'in native_identity' in text
         and 'native_identity(mode)' in text
         and 'During handling of the above exception' not in text
         and 'The above exception was the direct cause' not in text,
         'Original wrapper failure is not exclusively the known place-native route assertion')
    return {'session_id': 2330, 'driver_exit': 1, 'original_wrapper_passed': False,
            'error': ERROR, 'source_tool': receipt['source_tool']}


def native_place_identity(path):
    """Frozen full native checker; only snapshot binding and place command scope differ."""
    driver = module(DRIVER, DRIVER_SHA, 'postplace_original_driver')
    tree = ast.parse(DRIVER.read_bytes())
    original = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'native_identity')
    function = copy.deepcopy(original)
    function.name = 'postplace_native_identity'
    function.args.args.append(ast.arg(arg='snapshot'))
    path_assign = next(n for n in function.body if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == 'path' for t in n.targets))
    original_path = copy.deepcopy(path_assign.value)
    path_assign.value = ast.Name(id='snapshot', ctx=ast.Load())
    lists = [n for n in ast.walk(function) if isinstance(n, ast.List) and len(n.elts) == 3
             and all(isinstance(item, ast.Constant) for item in n.elts)
             and [item.value for item in n.elts] == ['place_design -directive ExtraNetDelay_high',
                 'phys_opt_design -directive AggressiveExplore', 'route_design -directive NoTimingRelaxation']]
    need(len(lists) == 1, 'Original native command whitelist changed')
    removed = lists[0].elts.pop()
    reverse = copy.deepcopy(function)
    reverse.name, reverse.args = original.name, copy.deepcopy(original.args)
    reverse_path = next(n for n in reverse.body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == 'path' for t in n.targets))
    reverse_path.value = original_path
    shortened = [n for n in ast.walk(reverse) if isinstance(n, ast.List) and len(n.elts) == 2
                 and all(isinstance(item, ast.Constant) for item in n.elts)
                 and [item.value for item in n.elts] == ['place_design -directive ExtraNetDelay_high',
                                                       'phys_opt_design -directive AggressiveExplore']]
    need(len(shortened) == 1, 'Native reverse whitelist changed')
    shortened[0].elts.append(removed)
    need(ast.dump(reverse, include_attributes=False) == ast.dump(original, include_attributes=False),
         'Native checker complete inverse AST differs')
    ast.fix_missing_locations(function)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(DRIVER), 'exec'), driver.__dict__)
    result = driver.postplace_native_identity('place', path)
    text = path.read_text().replace('\\', '/')
    steps = re.findall(r'^start_step (\S+)\s*$', text, re.MULTILINE)
    need(steps == ['init_design', 'opt_design', 'place_design', 'phys_opt_design']
         and not re.search(r'^\s*(route_design|write_bitstream)\b', text, re.MULTILINE),
         'Place native contains another stage, missing step or route/bit execution')
    synthesis = REF / 'fpai_demo_vivado.runs/synth_read_v3r7/ai7030_edif_top.dcp'
    need(sum(line.strip() == 'add_files -quiet ' + synthesis.as_posix() for line in text.splitlines()) == 1
         and sum(line.strip() == 'add_files ' + (REF / driver.BD_REL).as_posix() for line in text.splitlines()) == 1,
         'Actual place native lacks its unique new synthesis or managed BD source')
    result['path'] = str(NATIVE / 'ai7030_edif_top.tcl')
    proof = {'base_source_SHA256': DRIVER_SHA, 'inverse_complete_native_checker_AST_equal': True,
             'only_predicate_change': 'place requires place+physopt; no route or bit stage is permitted',
             'read_binding': 'frozen actual place native snapshot; original source path retained separately',
             'actual_steps': steps}
    return result, proof


def evaluate(directory, original_inventory, native_inventory, wrapper_sha):
    """Read frozen place values, current protected sources and the still-live physopt DCP."""
    source_guard()
    phase, native = directory / 'frozen-phase', directory / 'frozen-native'
    for base, rows in [(phase, original_inventory), (native, native_inventory)]:
        need(set(inventory(base)) == set(rows), 'Frozen evidence file set differs')
        for relative, expected in rows.items():
            actual = file_record(base / relative)
            need(actual == {k: expected[k] for k in ['bytes', 'SHA256']}, 'Frozen evidence bytes differ: ' + relative)
    need(sha(directory / 'wrapper-result.json') == wrapper_sha, 'Root merged wrapper result changed')
    outcome = wrapper_outcome(load(directory / 'wrapper-result.json'))
    driver = module(DRIVER, DRIVER_SHA, 'postplace_aa175_readonly')
    contract = module(CONTRACT, CONTRACT_SHA, 'postplace_fa28_readonly')
    prior = {mode: contract.completed(mode) for mode in ['setup', 'synthesis', 'constraints']}
    sources = driver.preflight()
    execution = load(phase / 'execution.json')
    need(type(execution.get('exit')) is int and execution['exit'] == 0
         and execution.get('stopped_by_monitor') is False and not execution.get('timeout', False),
         'Actual place tool failed, timed out or was stopped; recovery not applicable')
    need(sha(phase / 'actual-driver.py') == DRIVER_SHA
         and sha(phase / 'actual-supervisor.py') == OWNER_SHA, 'Actual place producer identity differs')
    proof = load(phase / 'input-proof.json')
    before, after = load(phase / 'OOC-cache-before.json'), load(phase / 'OOC-cache-after.json')
    expected = dict(sources)
    expected.update(OOC_cached_files_before=before, OOC_cache_policy=driver.CACHE_POLICY,
                    OOC_metadata_expected_paths=driver.metadata_paths(),
                    constraint_review_SHA256=sha(E / 'read-v3r7-constraints/review.json'),
                    parent_checkpoint=load(E / 'read-v3r7-synthesis/phase-artifacts.json')['native_checkpoint'])
    need(same(proof, expected), 'Place original input proof differs beyond the expected phase fields')
    cache = driver.compare_ooc_cache(before, after, driver.metadata_paths())
    need(same(cache, load(phase / 'OOC-cache-comparison.json')), 'Saved place OOC comparison differs')
    driver.compare_ooc_cache(after, driver.cached_ooc_inventory(), driver.metadata_paths())
    for relative in driver.metadata_paths():
        for label, rows in [('before', before), ('after', after)]:
            actual = file_record(phase / ('OOC-metadata-' + label) / relative)
            need(actual == {k: rows[relative][k] for k in ['bytes', 'SHA256']}, 'Saved metadata differs')
    need(sha(phase / 'implementation-profile.txt') == PROFILE_SHA, 'Complete original implementation profile differs')
    text = driver.build_tcl('place').replace('@@OUT@@', PHASE.as_posix()).replace(
        '@@REF@@', REF.as_posix()).replace('@@WORK@@', (W / 'read-v3r7-place').as_posix())
    need((phase / 'stage.tcl').read_text() == text, 'Actual place Tcl differs from frozen aa175 producer')
    output = (phase / 'stdout.txt').read_text(errors='replace')
    stderr = (phase / 'stderr.txt').read_text(errors='replace')
    need(sum(line.strip() == SENTINEL for line in output.splitlines()) == 1
         and not re.search(r'^ERROR:', output + '\n' + stderr, re.MULTILINE),
         'Actual completed place status/sentinel missing or tool error present')
    markers = ['.vivado.begin.rst', '.vivado.end.rst'] + [
        '.' + step + '.end.rst' for step in ['init_design', 'opt_design', 'place_design', 'phys_opt_design']]
    for name in markers:
        need((native / name).is_file(), 'Actual native completion marker missing: ' + name)
    need((native / '.vivado.begin.rst').stat().st_size > 0
         and all((native / name).stat().st_size == 0 for name in markers if name != '.vivado.begin.rst')
         and not any('.error.rst' in name or name == '.stop.rst' or name.startswith('.route_design.')
                     or name.startswith('.write_bitstream.') for name in native_inventory),
         'Actual native stage error/route/bit evidence exists')
    identity, adaptation = native_place_identity(native / 'ai7030_edif_top.tcl')
    need(sha(phase / 'fpai_demo_vivado.xpr') == load(phase / 'xpr-identity.json')['sha256'],
         'Actual place XPR snapshot identity differs')
    parent = expected['parent_checkpoint']
    need(same(parent, checkpoint(Path(parent['path']))), 'New synthesis parent checkpoint changed')
    exported = {'path': str(PHASE / 'ai7030_edif_top_physopt.dcp'),
                **file_record(phase / 'ai7030_edif_top_physopt.dcp')}
    physical = checkpoint(NATIVE / 'ai7030_edif_top_physopt.dcp')
    need(exported['bytes'] > 0, 'Actual exported physical checkpoint empty')
    return {'schema': 'r7-place-completion-audit-v1', 'passed': True,
            'original_wrapper_passed': False, 'original_wrapper': outcome,
            'wrapper_result_SHA256': wrapper_sha, 'original_phase_directory': str(PHASE),
            'original_phase_inventory': original_inventory, 'frozen_native_inventory': native_inventory,
            'auditor_path': str(SCRIPT), 'auditor_SHA256': START_SHA,
            'original_driver_SHA256': DRIVER_SHA, 'contract_SHA256': CONTRACT_SHA,
            'prior_phase_evidence': prior, 'input_proof_SHA256': sha(phase / 'input-proof.json'),
            'tool_execution_SHA256': sha(phase / 'execution.json'),
            'source_sha256': sources['source_sha256'], 'installed_sha256': sources['installed_sha256'],
            'preparation_review_SHA256': sha(driver.PREPARATION),
            'OOC_cache_comparison': cache, 'profile_SHA256': PROFILE_SHA,
            'native_source_identity': identity, 'native_predicate_adapter': adaptation,
            'exported_checkpoint': exported, 'native_checkpoint': physical, 'parent_checkpoint': parent,
            'native_markers': {name: file_record(native / name) for name in markers},
            'status_proof': 'original complete Tcl status/NEEDS_REFRESH assertions, tool exit0 and final sentinel',
            'route_executed': False, 'timing_or_board_acceptance': False,
            'EDA_repeated': False, 'new_timing_or_DRC_waiver': False}


def projection_payload(review, review_sha):
    identity = review['native_source_identity']
    producer = {'original_wrapper_passed': False, 'original_wrapper_exit': 1,
                'review_producer': 'independent-readonly-post-place-audit',
                'producer_review_path': str(AUDIT / 'review.json'), 'producer_review_SHA256': review_sha,
                'producer_source_path': str(SCRIPT), 'producer_source_SHA256': START_SHA,
                'recovery_reason': 'place-native-has-no-route-by-to_step-contract'}
    phase = {'passed': True, 'mode': 'place', 'preparation_review_SHA256': review['preparation_review_SHA256'],
             'source_count': 937, 'installed_count': 41, 'managed_PS_OOC_count': 11, 'OOC_cached_count': 24,
             'native': identity, 'checkpoint': review['exported_checkpoint'], 'candidate_run': 'impl_read_v3r7',
             'managed_run': True, 'parent_synthesis': 'synth_read_v3r7',
             'source_identity_unchanged_after_this_phase': True, 'OOC_cache_content_and_set_unchanged': True,
             'OOC_cache_nonmetadata_mtimes_unchanged': True,
             'OOC_metadata_mtime_policy': 'exact-24-gen-run-xml-mtime-only-v1',
             'OOC_cache_comparison_SHA256': review['original_phase_inventory']['OOC-cache-comparison.json']['SHA256'],
             'extra_r6_postroute_optimization': False, 'new_timing_or_DRC_waiver': False,
             'board_executed': False, 'bit_generation_implemented': False, **producer}
    artifacts = {'mode': 'place', 'native': identity, 'checkpoint': review['exported_checkpoint'],
                 'native_checkpoint': review['native_checkpoint'], 'parent_checkpoint': review['parent_checkpoint'],
                 'candidate_run': 'impl_read_v3r7', 'parent_synthesis': 'synth_read_v3r7', 'managed_run': True,
                 **producer}
    native = (AUDIT / 'frozen-native/ai7030_edif_top.tcl').read_bytes()
    payload = {'actual-native.tcl': native, 'native-script.tcl': native,
               'native-source-identity.json': raw_json(identity),
               'checkpoint-identity.json': raw_json(review['exported_checkpoint']),
               'phase-artifacts.json': raw_json(artifacts), 'phase-review.json': raw_json(phase)}
    records = {name: {'bytes': len(raw), 'SHA256': hashlib.sha256(raw).hexdigest()} for name, raw in payload.items()}
    payload['projection-provenance.json'] = raw_json({'schema': 'r7-place-exclusive-projection-v1',
        'producer': producer, 'original_files_never_overwritten': True,
        'original_phase_inventory_SHA256': hashlib.sha256(raw_json(review['original_phase_inventory'])).hexdigest(),
        'projected_files_except_this_descriptor': records, 'phase_review_is_last_canonical_file': True})
    return payload


def verify_audit():
    source_guard()
    review = load(AUDIT / 'review.json')
    recomputed = evaluate(AUDIT, review['original_phase_inventory'], review['frozen_native_inventory'],
                          review['wrapper_result_SHA256'])
    need(same(review, recomputed), 'Independent place audit differs from current frozen recomputation')
    payload = projection_payload(review, sha(AUDIT / 'review.json'))
    plan = {'schema': 'r7-place-projection-plan-v1', 'audit_review_SHA256': sha(AUDIT / 'review.json'),
            'auditor_SHA256': START_SHA, 'target_directory': str(PHASE), 'canonical_order': list(CANONICAL),
            'files': {name: {'bytes': len(raw), 'SHA256': hashlib.sha256(raw).hexdigest()}
                      for name, raw in payload.items()}}
    need(same(load(AUDIT / 'projection-plan.json'), plan), 'Projection plan differs')
    for name, raw in payload.items():
        need((AUDIT / 'projection-payload' / name).read_bytes() == raw, 'Planned canonical bytes differ')
    return review, plan, payload


def verify_projection(evidence=None):
    """Mandatory public pure gate, including a real complete publication receipt."""
    review, plan, payload = verify_audit()
    receipt = load(AUDIT / 'publication-complete.json')
    expected = {'schema': 'r7-place-publication-complete-v1', 'complete': True,
                'audit_review_SHA256': sha(AUDIT / 'review.json'),
                'projection_plan_SHA256': sha(AUDIT / 'projection-plan.json'), 'auditor_SHA256': START_SHA,
                'canonical_order': list(CANONICAL), 'phase_review_published_last': True,
                'original_wrapper_passed': False, 'original_files_unchanged': True, 'files': plan['files']}
    need(same(receipt, expected), 'Complete place publication receipt absent/incorrect')
    attempt = load(AUDIT / 'publication-attempt.json')
    need(same(attempt, {'audit_review_SHA256': expected['audit_review_SHA256'],
                        'projection_plan_SHA256': expected['projection_plan_SHA256'], 'auditor_SHA256': START_SHA}),
         'Exclusive publication attempt differs')
    actual = inventory(PHASE)
    need(set(actual) == set(review['original_phase_inventory']) | set(CANONICAL),
         'Original phase gained unexpected files or lost original evidence')
    for relative, row in review['original_phase_inventory'].items():
        need(same(actual[relative], row), 'Original phase bytes/mtime changed: ' + relative)
    for name, raw in payload.items():
        need((PHASE / name).read_bytes() == raw, 'Canonical projection bytes differ: ' + name)
    if evidence is not None:
        paths = [SCRIPT] + [p for p in AUDIT.rglob('*') if p.is_file()] + [PHASE / name for name in actual]
        for path in paths:
            value = sha(path)
            need(str(path.resolve()) not in evidence or evidence[str(path.resolve())] == value,
                 'Projection evidence changed within gate')
            evidence[str(path.resolve())] = value
    return {'audit_path': str(AUDIT / 'review.json'), 'audit_SHA256': expected['audit_review_SHA256'],
            'publication_path': str(AUDIT / 'publication-complete.json'),
            'publication_SHA256': sha(AUDIT / 'publication-complete.json'),
            'auditor_path': str(SCRIPT), 'auditor_SHA256': START_SHA,
            'original_wrapper_passed': False, 'independent_place_completion_pass': True,
            'native_checkpoint': review['native_checkpoint']}


def audit(wrapper_result):
    source_guard()
    need(not AUDIT.exists(), 'Preserve previous audit attempt; do not reuse')
    wrapper_outcome(load(wrapper_result))
    original = inventory(PHASE)
    need(not set(CANONICAL) & set(original), 'Canonical target already exists; no recovery overwrite')
    # Freeze before producing any review. An incomplete audit remains evidence,
    # never a pass. Later verification never compares live route-rewritten logs.
    AUDIT.mkdir()
    save_new(AUDIT / 'actual-auditor.py', START_BYTES)
    save_new(AUDIT / 'wrapper-result.json', wrapper_result.read_bytes())
    native_names = ['ai7030_edif_top.tcl', 'runme.log', 'gen_run.xml'] + [
        p.name for p in NATIVE.glob('.*.rst') if p.is_file()]
    native_names = sorted(set(native_names))
    native_records = {name: file_record(NATIVE / name, True) for name in native_names}
    for base, rows, output in [(PHASE, original, 'frozen-phase'), (NATIVE, native_records, 'frozen-native')]:
        for name in rows:
            target = AUDIT / output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(base / name, target)
    need(same(inventory(PHASE), original), 'Original place changed during audit freeze')
    review = evaluate(AUDIT, original, native_records, sha(AUDIT / 'wrapper-result.json'))
    save_new(AUDIT / 'review.json', raw_json(review))
    payload = projection_payload(review, sha(AUDIT / 'review.json'))
    for name, raw in payload.items():
        save_new(AUDIT / 'projection-payload' / name, raw)
    plan = {'schema': 'r7-place-projection-plan-v1', 'audit_review_SHA256': sha(AUDIT / 'review.json'),
            'auditor_SHA256': START_SHA, 'target_directory': str(PHASE), 'canonical_order': list(CANONICAL),
            'files': {name: {'bytes': len(raw), 'SHA256': hashlib.sha256(raw).hexdigest()}
                      for name, raw in payload.items()}}
    save_new(AUDIT / 'projection-plan.json', raw_json(plan))
    verify_audit()


def publish():
    source_guard()
    review, plan, payload = verify_audit()
    need(same(inventory(PHASE), review['original_phase_inventory']), 'Original phase changed before projection')
    need(not any((PHASE / name).exists() for name in CANONICAL), 'Projection target exists; preserve and stop')
    save_new(AUDIT / 'publication-attempt.json', raw_json({
        'audit_review_SHA256': sha(AUDIT / 'review.json'),
        'projection_plan_SHA256': sha(AUDIT / 'projection-plan.json'), 'auditor_SHA256': START_SHA}))
    # Durable exclusive attempt prevents a failed or partial publication retry.
    written = []
    try:
        for name in CANONICAL:
            source_guard()
            save_new(PHASE / name, payload[name])
            need((PHASE / name).read_bytes() == payload[name], 'Projection full readback failed')
            written.append(name)
        need(written[-1] == 'phase-review.json', 'Phase review was not the last canonical file')
        current = inventory(PHASE)
        need(all(same(current[name], row) for name, row in review['original_phase_inventory'].items()),
             'Original files changed during publication')
        save_new(AUDIT / 'publication-complete.json', raw_json({
            'schema': 'r7-place-publication-complete-v1', 'complete': True,
            'audit_review_SHA256': sha(AUDIT / 'review.json'),
            'projection_plan_SHA256': sha(AUDIT / 'projection-plan.json'), 'auditor_SHA256': START_SHA,
            'canonical_order': written, 'phase_review_published_last': True,
            'original_wrapper_passed': False, 'original_files_unchanged': True, 'files': plan['files']}))
        verify_projection()
    except BaseException:
        save_new(AUDIT / 'publication-failure.json', raw_json({'written': written, 'retry_permitted': False}))
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'audit', 'publish'], nargs='?', default='inspect')
    parser.add_argument('--wrapper-result', type=Path)
    args = parser.parse_args()
    source_guard()
    if args.mode == 'inspect':
        print(json.dumps({'read_only': True, 'audit_executed': False, 'published': False,
                          'EDA_or_board_started': False, 'auditor_SHA256': START_SHA,
                          'requires_actual_tool0_and_original_wrapper_known_failure': True}))
    elif args.mode == 'audit':
        need(args.wrapper_result is not None, 'Exact completed root tool result is required')
        audit(args.wrapper_result)
    else:
        need(args.wrapper_result is None, 'Publish consumes only its frozen audited outcome')
        publish()


if __name__ == '__main__':
    main()
