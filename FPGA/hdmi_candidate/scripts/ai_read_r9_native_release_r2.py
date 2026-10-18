"""Pure r9 routed/bit release gates. No CLI, tools, writes or board access.

The managed implementation identity is impl_read_v3r9. A separate future bit
session reopens its routed checkpoint without fabricating managed-run state.
"""
from pathlib import Path
import ast
import copy
import hashlib
import importlib.util
import json
import re
import types

R = Path(__file__).resolve().parents[3]
SCRIPTS = Path(__file__).resolve().parent
W = R / '.local/hdmi-live-20261018-r9'
E = R / 'tools/pose-v1/evidence/hdmi-live-20261018-r9'
SOFTWARE_E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REF = W / 'reference'
NATIVE = REF / 'fpai_demo_vivado.runs/bit_read_v3r9_r2'
CONTRACT = SCRIPTS / 'ai_read_r9_contract.py'
CONTRACT_SHA = 'd4212dfa4f917a1e44327442e25421a771773448be358fa84f6ecf96e96b4dc1'
REVIEW_ADAPTER = SCRIPTS / 'review_hdmi_reader_boundary_factory_route.py'
REVIEW_ADAPTER_SHA = '16adc4a988f59d7064d1fa19b26f9bd8765217341921ca84f103f0465bcdfc3b'
BIT_BASE = SCRIPTS / 'continue_ai_read_checkpoint.py'
BIT_BASE_SHA = 'ee11b66896bb84886b186a4667fd4d5c871ec7c404bcc034e56637bacd01504b'
PACKAGE_BASE = SCRIPTS / 'package_ai_read_offline.py'
PACKAGE_BASE_SHA = 'bf39a9e49a264d94b5033141560ac9c115c4b214faf104dac377a050e639ac3f'
BIT_ADAPTER = SCRIPTS / 'continue_hdmi_reader_boundary_bit_r2.py'
PACKAGE_ADAPTER = SCRIPTS / 'package_hdmi_reader_boundary_offline_r2.py'
OWNER = SCRIPTS / 'eda_owned_stage.py'
OWNER_SHA = '3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672'
BIT_DIR = E / 'read-v3r9-native-bit-r2'
FORMAL = E / 'read-v3r9-independent-reports-r1/review.json'
CANDIDATE = 'impl_read_v3r9'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def json_equal(left, right):
    """JSON identity also distinguishes booleans, integers and floating values."""
    return json.dumps(left, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(
        right, sort_keys=True, separators=(',', ':'), allow_nan=False)


def module(path, expected=None, name='r9_release_input'):
    raw = Path(path).read_bytes()
    need(expected is None or hashlib.sha256(raw).hexdigest() == expected,
         'Frozen source changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    # Execute the already checked bytes, not a later read by a source loader.
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


def contract():
    need(sha(REVIEW_ADAPTER) == REVIEW_ADAPTER_SHA, 'r9 routed adapter identity changed')
    return module(CONTRACT, CONTRACT_SHA, 'r9_release_fullflow_contract')


def source_closure():
    """Live dependencies become immutable stage/approval inputs, including this file."""
    fixed = {CONTRACT: CONTRACT_SHA, REVIEW_ADAPTER: REVIEW_ADAPTER_SHA,
             BIT_BASE: BIT_BASE_SHA, PACKAGE_BASE: PACKAGE_BASE_SHA, OWNER: OWNER_SHA}
    fixed.update({SCRIPTS / name: digest for name, digest in {
        'ai_read_postroute_contract.py': '37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b',
        'review_ai_read_route.py': '48a1506553804c2b033bbe41d527eca41a9f8b610bed6b32999f6cc89e60053c',
        'review_ai_read_constraints.py': '5b0ab899a632d0d732ab9192d559335c9f3fcca4695a146f449f3ff70e9644ae',
        'review_ai_read_r9_synthesis.py': '5f7e54d2942751c8fc3b3e26cc348a42fe6079cd2da70dfc7320510dc43b9fbb',
        'review_ai_read_r9_constraints.py': 'fa444ac72c5fad4c63d012fff841d27a5ace56694cdd6987d0499a89532094e0',
        'continue_ai_read_candidate.py': 'a100884326b044a6c054e8331255135a4e1231a53ad5d86def5ecf208100b55d',
        'continue_ai_monitor_candidate.py': 'e30ffbe3fb4231096ab19f6423daaf39994c2427ed52a73086ca07da8cc06941'
    }.items()})
    for path, expected in fixed.items():
        need(sha(path) == expected, 'Source closure changed: ' + str(path))
    fixed.update({SCRIPTS / name: digest for name, digest in {
        'continue_hdmi_reader_boundary_reports.py': '528fa208e01a3de18f3f312ce929458ea5c94dc59845dae2e4f036bf79f00967',
        'check_hdmi_reader_boundary_factory_drc.py': 'e145581d66ee31f66420a3b19338d49184711e3dfa367a66202f9bc844dd30fc',
        'continue_hdmi_reader_boundary_candidate.py': '3e65b5154282f5c714576bde337f01cb34cdf1a4197a7e0a4f072557d86991c5'
    }.items()})
    for path, expected in fixed.items():
        need(sha(path) == expected, 'Native consumption dependency changed: ' + str(path))
    paths = list(fixed) + [Path(__file__), BIT_ADAPTER, PACKAGE_ADAPTER]
    return {str(path.resolve()): sha(path) for path in sorted(paths)}


def record(evidence, path, expected=None):
    path = Path(path).resolve()
    actual = sha(path)
    need(expected is None or expected == actual, 'Evidence identity changed: ' + str(path))
    if evidence is not None:
        need(str(path) not in evidence or evidence[str(path)] == actual,
             'Evidence changed within gate: ' + str(path))
        evidence[str(path)] = actual
    return actual


def adapt_source(path, expected, changes, renames=()):
    """Exactly positioned literal/name edits with complete reverse-AST proof."""
    raw = Path(path).read_bytes()
    need(hashlib.sha256(raw).hexdigest() == expected, 'Frozen algorithm source changed')
    original = ast.parse(raw, filename=str(path))
    tree = copy.deepcopy(original)
    edited = []
    for kind, rows in [('Constant', changes), ('Name', renames)]:
        for line, col, old, new in rows:
            nodes = [n for n in ast.walk(tree) if type(n).__name__ == kind
                     and n.lineno == line and n.col_offset == col]
            need(len(nodes) == 1, 'AST whitelist position missing/ambiguous')
            node = nodes[0]
            attribute = 'value' if kind == 'Constant' else 'id'
            value = getattr(node, attribute)
            need(type(value) is type(old) and value == old, 'AST whitelist old value differs')
            setattr(node, attribute, new)
            edited.append({'kind': kind, 'line': line, 'column': col, 'old': old, 'new': new})
    reverse = copy.deepcopy(tree)
    for item in reversed(edited):
        matches = [n for n in ast.walk(reverse) if type(n).__name__ == item['kind']
                   and n.lineno == item['line'] and n.col_offset == item['column']]
        attribute = 'value' if item['kind'] == 'Constant' else 'id'
        need(len(matches) == 1 and getattr(matches[0], attribute) == item['new'],
             'AST inverse whitelist differs')
        setattr(matches[0], attribute, item['old'])
    need(ast.dump(reverse, include_attributes=False) == ast.dump(original, include_attributes=False),
         'Complete inverse algorithm AST differs')
    code = ast.unparse(tree).encode('utf-8') + b'\n'
    namespace = {'__file__': str(path), '__name__': 'r9_frozen_adapted_algorithms'}
    exec(compile(tree, str(path), 'exec'), namespace)
    proof = {'base_path': str(path), 'base_SHA256': expected, 'edits': edited,
             'inverse_complete_AST_equal': True, 'base___file___retained': True,
             'adapted_source_SHA256': hashlib.sha256(code).hexdigest()}
    return types.SimpleNamespace(**namespace, execution_namespace=namespace), proof, raw, code


PACKAGE_CHANGES = [
    (24, 18, 'tools/pose-v1/evidence/hdmi-live-20261017-r3', 'tools/pose-v1/evidence/hdmi-live-20261018-r9'),
    (25, 14, '.local/hdmi-live-20261017-r3', '.local/hdmi-live-20261018-r9'),
    (65, 27, 'read-v3r5-bit', 'read-v3r9-native-bit-r2'),
    (182, 38, 'read-v3r5-reports/review.json', 'read-v3r9-independent-reports-r1/review.json'),
    (185, 44, 'route_read_v3r5', CANDIDATE), (185, 95, False, True),
    (205, 42, 'route_read_v3r5', CANDIDATE), (205, 76, False, True),
    (207, 73, 'read-v3r5-bit/bit-identity.json', 'read-v3r9-native-bit-r2/bit-identity.json'),
    (279, 22, 'reference/fpai_demo_vivado.runs/route_read_v3r5/ai7030_edif_top.bit',
     'reference/fpai_demo_vivado.runs/bit_read_v3r9_r2/ai7030_edif_top.bit'),
    (307, 26, 'route_read_v3r5', CANDIDATE), (307, 60, False, True),
    (308, 9, 'r5_bit_gate', 'r9_bit_gate'),
    (318, 35, 'route_read_v3r5', CANDIDATE), (318, 81, False, True),
    (363, 31, 'route_read_v3r5', CANDIDATE), (363, 65, False, True),
    (379, 77, 'route_read_v3r5', CANDIDATE), (380, 38, False, True),
    (488, 13, 'r5_bit_gate', 'r9_bit_gate')]
PACKAGE_NAMES = [(384, 17, 'EVIDENCE', 'SOFTWARE_EVIDENCE'),
                 (389, 18, 'EVIDENCE', 'SOFTWARE_EVIDENCE')]


def package_algorithms():
    result, proof, raw, adapted = adapt_source(PACKAGE_BASE, PACKAGE_BASE_SHA,
                                                PACKAGE_CHANGES, PACKAGE_NAMES)
    result.execution_namespace['SOFTWARE_EVIDENCE'] = SOFTWARE_E
    return result, proof, raw, adapted


def routed_release(evidence=None):
    producer = SCRIPTS / 'review_hdmi_reader_boundary_factory_route.py'
    gate = module(producer, '16adc4a988f59d7064d1fa19b26f9bd8765217341921ca84f103f0465bcdfc3b', 'r9_current_native_report_gate')
    expected = gate.fresh_review()
    actual = load(FORMAL)
    need(json_equal(actual, expected) and actual.get('bit_generation_prerequisite_pass') is True
         and actual.get('new_timing_or_DRC_waiver') is False,
         'Actual accepted R9 final reports changed')
    continuation = actual['checkpoint_continuation']
    native = {'candidate_run': CANDIDATE, 'managed_run': True,
              'synthesis_checkpoint': contract().verify_synthesis()['synthesis_checkpoint'],
              'physical_checkpoint': continuation['source_physical_checkpoint'],
              'routed_checkpoint': continuation['routed_checkpoint'],
              'actual_phase_identity_evidence_SHA256': actual['actual_phase_identity_evidence_SHA256'],
              'source_preparation_review_SHA256': sha(contract().PREPARATION),
              'original_route_parent_phase_passed': False, 'original_route_parent_exit': 1,
              'legacy_field_semantics': 'fresh native source/checkpoint lineage; independent consumption accepted, not original parent acceptance'}
    profile = actual['factory_DRC_profile_reinstatement']
    return {'formal_review_path': str(FORMAL), 'formal_review_SHA256': record(evidence, FORMAL),
            'review_adapter_path': str(producer), 'review_adapter_SHA256': sha(producer),
            'contract_path': str(CONTRACT), 'contract_SHA256': CONTRACT_SHA,
            'fresh_fullflow': native, 'fixed_report_algorithm': actual['retained_routed_algorithm'],
            'factory_DRC_profile': profile}


class ReadTracker:
    def __init__(self, evidence):
        self.evidence = evidence

    def read(self, path, expected=None):
        record(self.evidence, path, expected)
        return Path(path).read_bytes()

    def json(self, path, expected=None):
        return json.loads(self.read(path, expected).decode('utf-8-sig'))


def pure_derived_verification(base, directory, bit_proof):
    """Run the unchanged derived proof body while omitting only its JSON write."""
    tree = ast.parse(BIT_BASE.read_bytes())
    original = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == 'bit_derived_verification')
    need(sha(BIT_BASE) == BIT_BASE_SHA and len(original.body) >= 3
         and isinstance(original.body[-3], ast.Assign)
         and isinstance(original.body[-2], ast.Expr)
         and isinstance(original.body[-2].value, ast.Call)
         and isinstance(original.body[-2].value.func, ast.Name)
         and original.body[-2].value.func.id == 'save_new'
         and isinstance(original.body[-1], ast.Return), 'Frozen derived write boundary differs')
    function = copy.deepcopy(original)
    function.name = 'r9_pure_derived_verification'
    function.body = function.body[:-3] + [ast.Return(value=ast.Name(id='result', ctx=ast.Load()))]
    inverse = copy.deepcopy(function)
    inverse.name = original.name
    inverse.body = inverse.body[:-1] + copy.deepcopy(original.body[-3:])
    need(ast.dump(inverse, include_attributes=False) == ast.dump(original, include_attributes=False),
         'Pure derived-verification reverse AST differs')
    ast.fix_missing_locations(function)
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(BIT_BASE), 'exec'), base.__dict__)
    return base.r9_pure_derived_verification(directory, bit_proof)


def verify_bit_release(evidence=None):
    """Actual bit exit, exact executed sources, full hooks/context and isolation."""
    released = routed_release(evidence)
    tracker = ReadTracker(evidence)
    execution = tracker.json(BIT_DIR / 'execution.json')
    phase = tracker.json(BIT_DIR / 'phase-review.json')
    need(type(execution.get('exit')) is int and execution['exit'] == 0
         and execution.get('stopped_by_monitor') is False and not execution.get('timeout', False)
         and phase.get('passed') is True and phase.get('mode') == 'bit'
         and phase.get('source_identity_unchanged') is True and phase.get('read_bits') == 2768
         and phase.get('candidate_run') == CANDIDATE and phase.get('managed_run') is True
         and phase.get('bit_generation_implemented') is True
         and phase.get('no_managed_run_status_used_or_fabricated') is True,
         'Actual r9 bit phase failed/incomplete')
    closure = source_closure()
    need(json_equal(tracker.json(BIT_DIR / 'source-closure.json'), closure),
         'Executed bit source/dependency closure differs')
    for path, digest in closure.items():
        tracker.read(path, digest)
    need(tracker.read(BIT_DIR / 'actual-driver.py') == tracker.read(BIT_ADAPTER),
         'Actual frozen r9 bit adapter differs')
    need(tracker.read(BIT_DIR / 'actual-supervisor.py', OWNER_SHA) == tracker.read(OWNER, OWNER_SHA),
         'Actual frozen bit supervisor differs')
    for i, (path, digest) in enumerate(closure.items()):
        tracker.read(BIT_DIR / ('input-source-%02d-' % i + Path(path).name), digest)
    driver = module(BIT_ADAPTER, closure[str(BIT_ADAPTER.resolve())], 'r9_release_actual_bit_adapter')
    prepared = driver.prepare()
    need(json_equal(tracker.json(BIT_DIR / 'input-proof.json'), prepared['input_proof'])
         and json_equal(tracker.json(BIT_DIR / 'bit-input-proof.json'), prepared['bit_proof']),
         'Actual r9 bit input/source/native transformation differs')
    base, _, _, _ = driver.bit_algorithms(released)
    identity_path = BIT_DIR / 'bit-identity.json'
    identity = tracker.json(identity_path)
    raw_path = NATIVE / 'ai7030_edif_top.bit'
    routed = released['fresh_fullflow']['routed_checkpoint']
    physical = released['fresh_fullflow']['physical_checkpoint']
    need(Path(phase.get('bit_identity_path', '')).resolve() == identity_path.resolve()
         and Path(identity.get('path', '')).resolve() == raw_path.resolve()
         and type(identity.get('bytes')) is int and 0 < identity['bytes'] == raw_path.stat().st_size
         and identity.get('SHA256') == record(evidence, raw_path)
         and identity.get('source_routed_checkpoint_SHA256') == routed['SHA256']
         and identity.get('source_physical_checkpoint_SHA256') == physical['SHA256']
         and identity.get('formal_routed_review_SHA256') == released['formal_review_SHA256']
         and identity.get('factory_hook_SHA256') == prepared['bit_proof']['factory_hook_SHA256']
         and json_equal(identity.get('r9_routed_release'), prepared['bit_proof']['r9_routed_release'])
         and json_equal(identity.get('r9_routed_release'), released)
         and json_equal(identity.get('context_verification'), base.bit_context_verification(BIT_DIR)),
         'Actual raw r9 bit identity/release/hooks/context differs')
    need((NATIVE / '.write_bitstream.end.rst').is_file()
         and not (NATIVE / '.write_bitstream.error.rst').exists(), 'Actual bit native completion absent')
    package, _, _, _ = package_algorithms()
    isolation = package.factory_derived_gate(tracker, prepared['input_proof']['source_sha256'], identity)
    need(json_equal(tracker.json(Path(identity['factory_derived_isolation']['path'])),
                    pure_derived_verification(base, BIT_DIR, prepared['bit_proof'])),
         'Raw factory writes/exec attempts do not reproduce the saved isolation proof')
    algorithms = module(SCRIPTS / 'review_ai_read_constraints.py',
                        '5b0ab899a632d0d732ab9192d559335c9f3fcca4695a146f449f3ff70e9644ae',
                        'r9_release_bit_endpoints')
    constraints = tracker.json(E / 'read-v3r9-constraints/review.json')
    indices = algorithms.parse_indices((BIT_DIR / 'checkpoint-binding.txt').read_text(), 'source', 'capture')
    need(json_equal(indices, constraints['read_indices'])
         and json_equal(phase.get('restored_snapshot_endpoint_bound'), algorithms.snapshot_endpoints(
             BIT_DIR / 'checkpoint-endpoints.txt', indices))
         and json_equal(phase.get('actual_clocks'), algorithms.clock_taps(BIT_DIR / 'clock-taps.txt', indices)),
         'Actual bit source/capture indices, endpoint timing or clocks differ')
    # Reconstruct the complete identity, rejecting unrecognized fields as well.
    wanted = {'path': str(raw_path), 'bytes': identity['bytes'], 'SHA256': identity['SHA256'],
              'source_routed_checkpoint_SHA256': routed['SHA256'],
              'source_physical_checkpoint_SHA256': physical['SHA256'],
              'formal_routed_review_SHA256': released['formal_review_SHA256'],
              'factory_hook_SHA256': prepared['bit_proof']['factory_hook_SHA256'],
              'context_verification': base.bit_context_verification(BIT_DIR),
              'factory_derived_isolation': identity['factory_derived_isolation'],
              'r9_routed_release': released}
    need(json_equal(identity, wanted), 'Unexpected r9 bit identity fields')
    for path in sorted(BIT_DIR.rglob('*')):
        if path.is_file():
            record(evidence, path)
    return {'candidate_run': CANDIDATE, 'managed_run': True,
            'release_helper_SHA256': record(evidence, Path(__file__)),
            'formal_review_SHA256': released['formal_review_SHA256'],
            'bit_identity_SHA256': record(evidence, identity_path),
            'routed_checkpoint_SHA256': routed['SHA256'], 'raw_bit_SHA256': identity['SHA256'],
            'source_preparation_review_SHA256': released['fresh_fullflow']['source_preparation_review_SHA256'],
            'r9_routed_release': released, 'factory_derived_isolation': isolation}
