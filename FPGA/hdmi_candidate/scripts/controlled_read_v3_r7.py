"""Isolated r7 Host candidate: fixed runtime algorithms, new source identities.

Default inspection is offline. This file never creates an approval, connects to
a board or activates a candidate. Source preparation is not board permission.
"""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import sys
from types import ModuleType

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent
OLD_WORK = ROOT / '.local/hdmi-live-20261017-r3'
E3 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
E7 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r7'
REF7 = ROOT / '.local/hdmi-live-20261017-r7/reference'
STATE = E3 / 'continuation-state.json'
MANIFEST = E7 / 'controlled-startup-read-v3/manifest.json'
REMOTE = '/root/hdmi-live-20261017-r7/'
RELEASE = SCRIPTS / 'ai_read_r7_release.py'
BIT_ADAPTER = SCRIPTS / 'continue_hdmi_reader_idle_bit.py'
PACKAGER = SCRIPTS / 'package_hdmi_reader_idle_offline.py'
# Filled only after the independently prepared sources have been frozen.
RELEASE_SHA256 = '306d401f30503f34eff8074d4f1bbff68fed4bb2be273b99001fe6e424ac0611'
BIT_ADAPTER_SHA256 = '359752dec92a2eeda16f43237de72546ad46a3e2aae67162f70a024d0fbd2d2c'
PACKAGER_SHA256 = '23248f1ef75c8c6f25eae9b8c1763d384ba6864e056aff5881b0c9acebf67c23'
BASES = {
    'planner': (OLD_WORK / 'controlled_read_v3.py', '7d170d0e800d5d9a9fe870628c65957d703f6b6fdd970ddbc28370b89a0a0154'),
    'generator': (OLD_WORK / 'prepare_remote_read_v3.py', '053404d5d29edf188821b82eb0243aa3300adfd68c19beb17a003feacc958099'),
    'executor': (OLD_WORK / 'execute_read_v3.py', '08e64fbeb4a21e5fe0f26629cdb098857b263961ae738c5ed6f94549033d26c3'),
    'startup_controller': (SCRIPTS / 'control_ai_read_startup.py', '8d2016d96cacddcdc16823519bff9b21ae00d883fe8d921193558a13914b25d4'),
    'secure_transport': (OLD_WORK / 'secure_transport.py', 'f6f96e83ade89b917b730201f57b118dce7fd400d2e23110f63a45a43fe18d0e')}
CANDIDATES = {
    'planner': Path(__file__), 'generator': SCRIPTS / 'prepare_remote_read_v3_r7.py',
    'executor': SCRIPTS / 'execute_read_v3_r7.py', 'startup_controller': SCRIPTS / 'control_ai_read_startup_r7.py',
    'secure_transport': SCRIPTS / 'secure_transport_read_v3_r7.py'}
_HOST_START_BYTES = Path(__file__).read_bytes()
_HOST_START_SHA256 = hashlib.sha256(_HOST_START_BYTES).hexdigest()
if globals().get('r7_loaded_source_SHA256', _HOST_START_SHA256) != _HOST_START_SHA256:
    raise ValueError('R7 Host file changed after its verified source bytes were loaded')
_CANDIDATE_START_SHA256 = {str(path.resolve()):
    (_HOST_START_SHA256 if role == 'planner' else hashlib.sha256(path.read_bytes()).hexdigest())
    for role, path in CANDIDATES.items()}
FIXED = {
    SCRIPTS / 'ai_read_r7_contract.py': 'fa28b01f12baf593788d554fae942564ff69753caf1310cd034a48d08178fdc8',
    SCRIPTS / 'review_ai_read_r7_synthesis.py': '54919b9fd2bd9c7bd333282e1049d911c654511a961db1ae9fc2b753e90fc78b',
    SCRIPTS / 'review_ai_read_r7_constraints.py': '9937d6b2d93801b6b7b8b784cb23e798c6a597acc495751b9d13053629a7f478',
    SCRIPTS / 'review_ai_read_r7_route.py': 'abb512d4d148a6b73e8f4fdbcc75b4b8112670798dd72ffeba6a911712793af2'}
_PLANNER = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def json_equal(left, right):
    return json.dumps(left, sort_keys=True, separators=(',', ':')) == json.dumps(right, sort_keys=True, separators=(',', ':'))


def source_closure():
    """Manifest-owned byte closure; mutable runtime state is deliberately read live."""
    candidate_sources_unchanged()
    fixed = {path: expected for path, expected in BASES.values()}
    fixed.update(FIXED)
    fixed.update({RELEASE: RELEASE_SHA256, BIT_ADAPTER: BIT_ADAPTER_SHA256, PACKAGER: PACKAGER_SHA256})
    for path, expected in fixed.items():
        need(isinstance(expected, str) and len(expected) == 64 and sha(path) == expected,
             'Unfrozen/changed r7 Host source dependency: ' + str(path))
    paths = set(fixed) | set(CANDIDATES.values())
    result = {str(path.resolve()): sha(path) for path in sorted(paths)}
    inherited = _release_module().source_closure()
    need(isinstance(inherited, dict) and len(inherited) == 15, 'Complete r7 release source closure differs')
    for path, expected in inherited.items():
        actual = Path(path)
        need(actual.is_absolute() and actual.resolve().is_relative_to(ROOT.resolve())
             and sha(actual) == expected and (str(actual.resolve()) not in result or result[str(actual.resolve())] == expected),
             'R7 release source dependency differs: ' + path)
        result[str(actual.resolve())] = expected
    return result


def _release_module():
    raw = RELEASE.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == RELEASE_SHA256, 'Frozen r7 release helper changed')
    module = ModuleType('r7_host_frozen_release')
    module.__file__ = str(RELEASE)
    exec(compile(raw, str(RELEASE), 'exec'), vars(module))
    return module


def release():
    source_closure()
    return _release_module()


def onsite_guard(action, state):
    """Pure state predicate; real callers always read the fixed current STATE."""
    need(isinstance(state, dict) and not str(state.get('status', '')).startswith('paused'), 'Current task is paused')
    if action in {'install_candidate', 'uart_candidate', 'candidate_reboot', 'shared_three',
                  'uart_fallback', 'original_fallback_reboot'}:
        onsite = state.get('onsite_observation_work')
        need(isinstance(onsite, dict) and onsite.get('paused') is False,
             'Onsite observation work paused or not explicitly resumed; no candidate install/start/HDMI action')


def current_guard(action):
    candidate_sources_unchanged()
    onsite_guard(action, json.loads(STATE.read_text(encoding='utf-8-sig')))


def candidate_sources_unchanged():
    for path, expected in _CANDIDATE_START_SHA256.items():
        need(sha(Path(path)) == expected, 'R7 Host candidate source changed after process start: ' + path)


def checked_candidate_import(name, path):
    """Public adapter import callback: compile the same single verified read."""
    candidate_sources_unchanged()
    path = Path(path).resolve()
    need(str(path) in _CANDIDATE_START_SHA256, 'Unexpected r7 Host import path: ' + str(path))
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == _CANDIDATE_START_SHA256[str(path)],
         'R7 Host import source changed before compilation: ' + str(path))
    module = ModuleType(name)
    module.__file__ = str(path)
    module.r7_loaded_source_SHA256 = _CANDIDATE_START_SHA256[str(path)]
    exec(compile(raw, str(path), 'exec'), vars(module))
    return module


def _adapted(role):
    path, expected = BASES[role]
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'Frozen original Host algorithm changed: ' + role)
    original, tree = ast.parse(raw), ast.parse(raw)
    edits, replacements = [], []

    def literal(function, old, new, count):
        node = next(item for item in tree.body if isinstance(item, ast.FunctionDef) and item.name == function)
        matches = [item for item in ast.walk(node) if isinstance(item, ast.Constant) and type(item.value) is type(old) and item.value == old]
        need(len(matches) == count, 'Host literal identity/count changed: ' + role + '/' + function + '/' + str(old))
        for item in matches:
            edits.append({'function': function, 'line': item.lineno, 'column': item.col_offset, 'old': old, 'new': new})
            item.value = new

    if role == 'planner':
        for old, new, count in [
            ('read-v3r3-synthesis', 'read-v3r7-synthesis', 1),
            ('read-v3r3-constraints-r3', 'read-v3r7-constraints', 1),
            ('synth_read_v3r3', 'synth_read_v3r7', 1),
            ('.local/hdmi-live-20261017-r3/reference', '.local/hdmi-live-20261017-r7/reference', 1),
            ('/root/hdmi-live-20261017-r3/', REMOTE, 1),
            ('build-read-probe-r2/ai_read_dma_probe', str(E3 / 'build-read-probe-r2/ai_read_dma_probe'), 1),
            ('read-shared-build-r2/package.tar', str(E3 / 'read-shared-build-r2/package.tar'), 1),
            ('read-shared-build-r2/package-files.json', str(E3 / 'read-shared-build-r2/package-files.json'), 3),
            ('resume-board-readonly/result.json', str(E3 / 'resume-board-readonly/result.json'), 3)]:
            literal('review_manifest', old, new, count)
        literal('require_approval', 'continuation-state.json', str(STATE), 1)
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'review_manifest')
        old_gate = next((i for i, node in enumerate(function.body) if isinstance(node, ast.Expr)
                         and any(isinstance(item, ast.Constant) and item.value == 'ICAP package lacks the complete actual r6 optimization lineage gate' for item in ast.walk(node))), None)
        need(old_gate is not None, 'Frozen r6-only release assertion changed')
        replacement = ast.parse("need(r7_json_equal(patch.get('r7_bit_gate'), lineage['r7_bit_gate']) and r7_json_equal(boot.get('r7_bit_gate'), lineage['r7_bit_gate']), 'ICAP/BOOT package lacks the actual r7 fullflow/bit release gate')").body[0]
        replacements.append((function.name, old_gate, copy.deepcopy(function.body[old_gate])))
        function.body[old_gate] = replacement
        packaging = next(node for node in function.body if isinstance(node, ast.Expr)
                         and any(isinstance(item, ast.Constant) and item.value == 'Packaging review uses an older implementation or managed run' for item in ast.walk(node)))
        flags = [item for item in ast.walk(packaging) if isinstance(item, ast.Constant) and item.value is False]
        need(len(flags) == 2, 'Frozen package managed-run assertion changed')
        for item in flags:
            edits.append({'function': function.name, 'line': item.lineno, 'column': item.col_offset, 'old': False, 'new': True})
            item.value = True
        returned = function.body[-1].value.elts[1]
        managed = [i for i, key in enumerate(returned.keys) if isinstance(key, ast.Constant) and key.value == 'managed_run']
        need(len(managed) == 1 and returned.values[managed[0]].value is False, 'Frozen planner result identity changed')
        item = returned.values[managed[0]]
        edits.append({'function': function.name, 'line': item.lineno, 'column': item.col_offset, 'old': False, 'new': True})
        item.value = True
    elif role == 'generator':
        for function in ['load_planner', 'actual_configuration', 'check_local_stage']:
            literal(function, 'controlled_read_v3.py', 'controlled_read_v3_r7.py', 1)
        literal('check_local_stage', 'continuation-state.json', str(STATE), 1)
    elif role == 'executor':
        literal('generator', 'prepare_remote_read_v3.py', 'prepare_remote_read_v3_r7.py', 1)
        literal('transport_options', 'secure_transport.py', 'secure_transport_read_v3_r7.py', 2)
        literal('transport_options', '/root/hdmi-live-20261017-r3/', REMOTE, 1)
    elif role == 'startup_controller':
        literal('configuration', 'prepare_remote_read_v3.py', 'prepare_remote_read_v3_r7.py', 1)
        literal('transport', 'execute_read_v3.py', 'execute_read_v3_r7.py', 1)
        literal('capture_source', 'continuation-state.json', str(STATE), 1)
        literal('reboot', 'continuation-state.json', str(STATE), 1)

    restored = copy.deepcopy(tree)
    for change in edits:
        function = next(node for node in restored.body if isinstance(node, ast.FunctionDef) and node.name == change['function'])
        matches = [node for node in ast.walk(function) if isinstance(node, ast.Constant)
                   and node.lineno == change['line'] and node.col_offset == change['column']]
        need(len(matches) == 1 and type(matches[0].value) is type(change['new']) and matches[0].value == change['new'],
             'Host inverse literal identity changed')
        matches[0].value = change['old']
    for function_name, index, node in replacements:
        function = next(item for item in restored.body if isinstance(item, ast.FunctionDef) and item.name == function_name)
        function.body[index] = node
    need(ast.dump(restored, include_attributes=False) == ast.dump(original, include_attributes=False), 'Host adapter complete inverse AST failed')
    module = ModuleType('isolated_r7_' + role)
    module.__file__ = str(CANDIDATES[role])
    exec(compile(ast.fix_missing_locations(tree), str(path) + ' [r7 explicit Host identities]', 'exec'), vars(module))
    proof = {'role': role, 'base_source_path': str(path), 'base_source_SHA256': expected,
             'effective___file__': str(CANDIDATES[role]), 'literal_edits': edits,
             'r6_only_assertion_replaced': bool(replacements), 'complete_inverse_AST_equal': True,
             'raw_remote_COMMON_or_CAPTURE_changed': False}
    return module, proof


def _lineage(constraints, route, evidence):
    gate = release().verify_bit_release(evidence)
    need(gate['candidate_run'] == 'impl_read_v3r7' and gate['managed_run'] is True,
         'Actual r7 bit/fullflow source identity differs')
    need(constraints['source_sha256'] == route['source_sha256']
         and route['candidate_run'] == 'impl_read_v3r7' and route['managed_run'] is True,
         'Actual r7 constraints/routed gate identities differ')
    closure = source_closure()
    need(all(path not in evidence or evidence[path] == value for path, value in closure.items()),
         'Source evidence changed within r7 Host review')
    evidence.update(closure)
    return {'candidate_run': 'impl_read_v3r7', 'managed_run': True, 'r7_bit_gate': gate,
            'fresh_fullflow': gate['r7_routed_release']['fresh_fullflow'],
            'old_r6_checkpoint_or_optimization_reused': False}


def planner():
    global _PLANNER
    if _PLANNER is None:
        module, proof = _adapted('planner')
        module.E, module.REFERENCE, module.RUN, module.MANIFEST = E7, REF7, 'impl_read_v3r7', MANIFEST
        module.POSTROUTE_PACKAGER = PACKAGER
        module.ADAPTER_PATHS = CANDIDATES
        historical = {'observer_unit': 'sim-ai-read-monitor-r1/result.json', 'managed_PS': 'managed-PS-observer-r2/review.json',
                      'toolchain': 'toolchain-identity.json', 'probe_build': 'build-read-probe-r2/result.json',
                      'shared_build': 'read-shared-build-r2/result.json', 'epoch_mock': 'mock-ai-read-monitor-r1/run-r2/result.json'}
        current = {'constraints': 'read-v3r7-constraints/review.json', 'route': 'read-v3r7-reports/review.json',
                   'icap': 'read-v3-icap/review.json', 'boot': 'read-v3-boot/review.json'}
        module.GATE_PATHS = {name: str(E3 / relative) for name, relative in historical.items()}
        module.GATE_PATHS.update({name: str(E7 / relative) for name, relative in current.items()})
        module.verify_checkpoint_lineage = _lineage
        module.r7_json_equal = json_equal
        module.r7_adapter_proof = proof
        module.review_manifest = review_manifest
        module.require_approval = require_approval
        _PLANNER = module
    return _PLANNER


def review_manifest():
    # A missing actual r7 release closes entry before any runtime/transport path.
    release().verify_bit_release({})
    module = planner()
    original, _ = _adapted('planner')
    original.__dict__.update({name: value for name, value in vars(module).items()
                              if name in {'E', 'REFERENCE', 'RUN', 'MANIFEST', 'POSTROUTE_PACKAGER', 'ADAPTER_PATHS',
                                          'GATE_PATHS', 'verify_checkpoint_lineage', 'r7_json_equal'}})
    context, review = original.review_manifest()
    closure = source_closure()
    need(json_equal(context.get('source_closure'), closure), 'Manifest r7 Host/runtime/build source closure differs')
    review.update(r7_source_closure=closure, r7_Host_adapter_proof=module.r7_adapter_proof)
    return context, review


def require_approval(action, context, approved, receipt):
    current_guard(action)
    actual_context, _ = review_manifest()
    need(context.get('_local_review_sha256') == actual_context.get('_local_review_sha256'), 'Actual r7 local review changed')
    original, _ = _adapted('planner')
    original.E, original.MANIFEST = E7, MANIFEST
    return original.require_approval(action, context, approved, receipt)


def adapter(role):
    need(role in BASES and role != 'planner', 'Unknown r7 Host adapter role')
    candidate_sources_unchanged()
    module, proof = _adapted(role)
    if role in {'generator', 'executor'}:
        module.WORK, module.EVIDENCE = SCRIPTS, E7
    if role == 'generator':
        module.BASE = REMOTE.rstrip('/')
        module.load_planner = planner
        original_check = module.check_local_stage

        def check_local_stage(stage, generation_dir, approved, receipt):
            current_guard(module.STAGES.get(stage))
            return original_check(stage, generation_dir, approved, receipt)

        module.check_local_stage = check_local_stage
        proof['dynamic_pause_checked_before_stage_review'] = True
    elif role == 'executor':
        module.imported = checked_candidate_import
        original_entry = module.entry

        def entry(stage, generation_dir, approved, receipt):
            current_guard(module.generator().STAGES.get(stage))
            return original_entry(stage, generation_dir, approved, receipt)

        module.entry = entry
        proof['dynamic_pause_checked_before_stage_review'] = True
    elif role == 'startup_controller':
        module.WORK, module.EVIDENCE = SCRIPTS, E7
        module.import_file = checked_candidate_import
        original_approval = module.approval

        def approval(action, approved, receipt):
            current_guard(action)
            return original_approval(action, approved, receipt)

        module.approval = approval
        proof['dynamic_pause_checked_before_startup_review'] = True
        original_capture_source = module.capture_source

        def capture_source(configuration, kind, receipt):
            source = original_capture_source(configuration, kind, receipt)
            marker = "    if ($taskLive.status -like 'paused*') {throw 'Task paused before UART open'}"
            guard = ("    if ($null -eq $taskLive.onsite_observation_work -or "
                     "($taskLive.onsite_observation_work -isnot [System.Management.Automation.PSCustomObject] -and "
                     "$taskLive.onsite_observation_work -isnot [System.Collections.IDictionary]) -or "
                     "$taskLive.onsite_observation_work.paused -isnot [bool] -or "
                     "$taskLive.onsite_observation_work.paused) {throw 'Onsite observation work paused before UART open'}")
            need(source.count(marker) == 1, 'Original child pause boundary changed')
            return source.replace(marker, marker + '\n' + guard, 1)

        module.capture_source = capture_source
        proof['child_onsite_boolean_guard_added_before_UART_create'] = True
    elif role == 'secure_transport':
        module.REMOTE = REMOTE
    module.r7_adapter_proof = proof
    return module


def source_preparation(role=None):
    roles = [role] if role else list(BASES)
    proofs = [_adapted(name)[1] if name == 'planner' else adapter(name).r7_adapter_proof for name in roles]
    return {'source_preparation_only': True, 'algorithm_adapters': proofs,
            'runtime_state_path': str(STATE), 'manifest_path': str(MANIFEST),
            'r7_source_closure': source_closure(),
            'r7_fullflow_and_bit_release_still_required': True, 'specific_user_package_permission_still_required': True,
            'board_or_network_or_UART_actions_executed': False}


def __getattr__(name):
    if name.startswith('_'):
        raise AttributeError(name)
    return getattr(planner(), name)


def main():
    if sys.argv[1:] == ['--source-check']:
        print(json.dumps(source_preparation(), ensure_ascii=False, indent=2))
        return 0
    return planner().main()


if __name__ == '__main__':
    raise SystemExit(main())
