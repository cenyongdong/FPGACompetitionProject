"""R7 bit-only adapter. Default inspect is pure; explicit bit is one offline job.

This does not modify the managed fullflow driver, launch a managed run, process
ICAP/BOOT, connect to a device or grant deployment/reboot permission.
"""
from pathlib import Path
import argparse
import ast
import copy
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parent
RELEASE_PATH = SCRIPTS / 'ai_read_r9_native_release.py'


def release():
    spec = importlib.util.spec_from_file_location('r9_bit_public_release', RELEASE_PATH)
    module = importlib.util.module_from_spec(spec)
    exec(compile(RELEASE_PATH.read_bytes(), str(RELEASE_PATH), 'exec'), module.__dict__)
    return module


def factory_preflight_adapter(helper, base):
    """Retain every factory/native/derived check; replace only old phase lineage."""
    original = ast.parse(helper.BIT_BASE.read_bytes())
    function = next(n for n in original.body if isinstance(n, ast.FunctionDef) and n.name == 'bit_preflight')
    helper.need(len(function.body) == 21, 'Frozen bit preflight statement count differs')
    omitted = [1, 8, 11, 12]
    adapted = copy.deepcopy(function)
    adapted.name = 'r9_factory_preflight'
    adapted.args.args.append(ast.arg(arg='routed'))
    adapted.body = [copy.deepcopy(n) for i, n in enumerate(function.body) if i not in omitted]
    nodes = [n for n in ast.walk(adapted) if isinstance(n, ast.Constant)
             and n.value == 'read-v3r5-bit/factory-derived']
    helper.need(len(nodes) == 1, 'Frozen derived directory literal differs')
    nodes[0].value = 'read-v3r9-native-bit-r1/factory-derived'
    inverse = copy.deepcopy(adapted)
    inverse.name = function.name
    inverse.args = copy.deepcopy(function.args)
    for node in ast.walk(inverse):
        if isinstance(node, ast.Constant) and node.value == 'read-v3r9-native-bit-r1/factory-derived':
            node.value = 'read-v3r5-bit/factory-derived'
    retained = iter(inverse.body)
    inverse.body = [copy.deepcopy(function.body[i]) if i in omitted else next(retained)
                    for i in range(len(function.body))]
    helper.need(ast.dump(inverse, include_attributes=False) == ast.dump(function, include_attributes=False),
                'Factory preflight reverse AST differs')
    ast.fix_missing_locations(adapted)
    code = ast.Module(body=[adapted], type_ignores=[])
    exec(compile(code, str(helper.BIT_BASE), 'exec'), base.__dict__)
    proof = {'base_path': str(helper.BIT_BASE), 'base_SHA256': helper.BIT_BASE_SHA,
             'original_statement_count': 21, 'omitted_statement_indices': omitted,
             'replacement': 'actual r9 fullflow/formal report and explicit actual routed identity',
             'derived_directory_change': ['read-v3r5-bit/factory-derived', 'read-v3r9-native-bit-r1/factory-derived'],
             'inverse_complete_preflight_AST_equal': True,
             'adapted_function_SHA256': hashlib.sha256(ast.unparse(code).encode()).hexdigest()}
    return base.r9_factory_preflight, proof


def bit_algorithms(released):
    helper = release()
    base = helper.module(helper.BIT_BASE, helper.BIT_BASE_SHA, 'r9_complete_factory_bit_algorithms')
    base.W, base.E, base.REF, base.NATIVE = helper.W, helper.E, helper.REF, helper.NATIVE
    fullflow = released['fresh_fullflow']
    base.CHECKPOINT = Path(fullflow['physical_checkpoint']['path'])
    base.CHECKPOINT_SHA = fullflow['physical_checkpoint']['SHA256']
    base.ROUTED = Path(fullflow['routed_checkpoint']['path'])
    base.BIT_REVIEW, base.BIT = helper.FORMAL, helper.NATIVE / 'ai7030_edif_top.bit'
    original_pieces = base.pieces

    def bound_pieces():
        header, route, endpoints, reports = original_pieces()
        # Only the passive managed-PS byte comparison refers to historical E3.
        # All design/checkpoint/output paths remain the independent new REF7.
        helper.need(endpoints.count('@@EVIDENCE@@') == 2, 'Managed PS template receipt count differs')
        endpoints = endpoints.replace('@@EVIDENCE@@', helper.SOFTWARE_E.as_posix())
        return header, route, endpoints, reports

    base.pieces = bound_pieces
    function, proof = factory_preflight_adapter(helper, base)
    proof['managed_PS_template_binding'] = {
        'original_template_placeholders': 2, 'source_provenance_receipt_root': str(helper.SOFTWARE_E),
        'actual_design_root': str(helper.REF), 'other_original_Tcl_algorithms_unchanged': True}
    return base, function, proof, helper


def prepare():
    helper = release()
    released = helper.routed_release()
    base, factory_preflight, adaptation, _ = bit_algorithms(released)
    contract = helper.contract()
    sources = contract.stable_sources()
    installed = contract.installed_identity()
    lineage = released['fresh_fullflow']
    proof = {'source_sha256': sources, 'installed_sha256': installed['actual'],
             'installed_identity_ledger_SHA256': helper.sha(contract.INSTALLED),
             'preparation_review_SHA256': helper.sha(contract.PREPARATION),
             'physical_checkpoint': lineage['physical_checkpoint'],
             'routed_checkpoint': lineage['routed_checkpoint'],
             'candidate_run': helper.CANDIDATE, 'managed_run': True,
             'source_closure': helper.source_closure(),
             'new_timing_or_DRC_waiver': False, 'new_BOOT_reboot_permission': False}
    routed = dict(lineage['routed_checkpoint'])
    routed['source_physical_checkpoint_SHA256'] = lineage['physical_checkpoint']['SHA256']
    bit_proof = factory_preflight(proof, routed)
    bit_proof['r9_routed_release'] = released
    bit_proof['factory_preflight_adapter'] = adaptation
    tcl = base.build_tcl('bit')
    helper.need('@@EVIDENCE@@' not in tcl
                and 'open_checkpoint {' + Path(routed['path']).as_posix() + '}' in tcl
                and 'route_read_v3r5' not in tcl and 'launch_runs' not in tcl
                and 'phys_opt_design -placement_opt' not in tcl,
                'R7 bit source contains an old checkpoint/run or new implementation step')
    return {'input_proof': proof, 'bit_proof': bit_proof, 'tcl': tcl}


def save_new(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['inspect', 'bit'], nargs='?', default='inspect')
    args = parser.parse_args()
    helper = release()
    driver_raw = Path(__file__).read_bytes()
    prepared = prepare()  # Missing actual routed release fails before any mkdir/tool.
    if args.mode == 'inspect':
        print(json.dumps({'inspect_only': True, 'EDA_started': False, 'board_executed': False,
                          'Tcl_bytes': len(prepared['tcl'].encode()), 'r9_routed_release':
                          prepared['bit_proof']['r9_routed_release']}, indent=2))
        return 0
    out, work = helper.BIT_DIR, helper.W / 'read-v3r9-native-bit-r1'
    helper.need(not out.exists() and not work.exists(), 'Preserve existing bit stage; no retry')
    base, _, _, _ = bit_algorithms(prepared['bit_proof']['r9_routed_release'])
    helper.need(base.NATIVE.is_dir() and not any((base.NATIVE / name).exists() for name in
                ['ai7030_edif_top.bit', '.write_bitstream.begin.rst', '.write_bitstream.end.rst',
                 '.write_bitstream.error.rst']), 'Native bit target already used; stop')
    closure = helper.source_closure()
    frozen = {path: Path(path).read_bytes() for path in closure}
    helper.need(closure == prepared['input_proof']['source_closure']
                and hashlib.sha256(driver_raw).hexdigest() == closure[str(Path(__file__).resolve())]
                and all(hashlib.sha256(raw).hexdigest() == closure[path] for path, raw in frozen.items()),
                'Frozen execution bytes changed before bit launch')
    before = {name: (helper.REF / name).read_bytes() if (helper.REF / name).exists() else None
              for name in base.DERIVED_NAMES}
    owner = helper.module(helper.OWNER, helper.OWNER_SHA, 'r9_bit_owned_stage')
    owner.E, owner.W = helper.E, helper.W
    try:
        owner.stage('read-v3r9-native-bit-r1', prepared['tcl'], ceiling=540, run_names=[helper.CANDIDATE])
    finally:
        if out.exists():
            (out / 'actual-driver.py').write_bytes(driver_raw)
            save_new(out / 'input-proof.json', prepared['input_proof'])
            save_new(out / 'bit-input-proof.json', prepared['bit_proof'])
            save_new(out / 'source-closure.json', closure)
            for i, (path, raw) in enumerate(frozen.items()):
                (out / ('input-source-%02d-' % i + Path(path).name)).write_bytes(raw)
            save_new(out / 'native-after.json', base.native_inventory())
            base.preserve_derived_outputs(out, before)
    helper.need(prepare() == prepared and helper.source_closure() == closure,
                'Source/release/native template changed during bit generation')
    helpers = helper.module(helper.SCRIPTS / 'review_ai_read_constraints.py',
                            '5b0ab899a632d0d732ab9192d559335c9f3fcca4695a146f449f3ff70e9644ae',
                            'r9_bit_endpoint_algorithms')
    gate = helper.load(helper.E / 'read-v3r9-constraints/review.json')
    indices = helpers.parse_indices((out / 'checkpoint-binding.txt').read_text(), 'source', 'capture')
    helper.need(indices == gate['read_indices'], 'Restored r9 bit endpoint indices differ')
    endpoints = helpers.snapshot_endpoints(out / 'checkpoint-endpoints.txt', indices)
    clocks = helpers.clock_taps(out / 'clock-taps.txt', indices)
    helper.need(base.BIT.is_file() and base.BIT.stat().st_size > 0
                and (base.NATIVE / '.write_bitstream.end.rst').is_file()
                and not (base.NATIVE / '.write_bitstream.error.rst').exists(), 'Bit native completion missing')
    context = base.bit_context_verification(out)
    derived = base.bit_derived_verification(out, prepared['bit_proof'])
    proof = prepared['bit_proof']
    identity_path = out / 'bit-identity.json'
    save_new(identity_path, {'path': str(base.BIT), 'bytes': base.BIT.stat().st_size,
             'SHA256': helper.sha(base.BIT),
             'source_routed_checkpoint_SHA256': proof['source_routed_checkpoint_SHA256'],
             'source_physical_checkpoint_SHA256': proof['source_physical_checkpoint_SHA256'],
             'formal_routed_review_SHA256': proof['formal_routed_review_SHA256'],
             'factory_hook_SHA256': proof['factory_hook_SHA256'], 'context_verification': context,
             'factory_derived_isolation': derived, 'r9_routed_release': proof['r9_routed_release']})
    save_new(out / 'phase-review.json', {'passed': True, 'mode': 'bit', 'source_identity_unchanged': True,
             'read_bits': len(indices), 'restored_snapshot_endpoint_bound': endpoints, 'actual_clocks': clocks,
             'no_managed_run_status_used_or_fabricated': True, 'candidate_run': helper.CANDIDATE,
             'managed_run': True, 'bit_identity_path': str(identity_path), 'bit_generation_implemented': True,
             'execution_mode': 'independent checkpoint bit job; managed_run describes upstream candidate only',
             'new_BOOT_reboot_permission': False, 'board_executed': False})
    print(json.dumps({'phase': 'read-v3r9-native-bit-r1', 'passed': True, 'board_acceptance': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
