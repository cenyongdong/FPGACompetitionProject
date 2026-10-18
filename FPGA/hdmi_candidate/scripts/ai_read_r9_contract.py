"""Read-only r7 source/phase bindings and frozen report algorithms; no EDA.

Old results identify source provenance only. Every accepted implementation
result must be produced again under the new reference and new stage names.
"""
from pathlib import Path
import ast
import copy
import difflib
import hashlib
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from types import ModuleType

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
E3 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
E = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261018-r9'
REF = ROOT / '.local/hdmi-live-20261018-r9/reference'
OLD_REF = ROOT / '.local/hdmi-live-20261017-r3/reference'
PREPARATION = E / 'preparation/review.json'
SAFETY = E / 'preparation-safety-r2/review.json'
DRIVER_SHA = '3e65b5154282f5c714576bde337f01cb34cdf1a4197a7e0a4f072557d86991c5'
SUPERVISOR_SHA = '3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672'
INSTALLED = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/toolchain-identity-review.json'
TOOL = Path('D:/vivado18.3/Vivado/2018.3')
SCRIPTS = Path(__file__).parent
CONSTRAINTS = SCRIPTS / 'review_ai_read_constraints.py'
CONSTRAINTS_SHA = '5b0ab899a632d0d732ab9192d559335c9f3fcca4695a146f449f3ff70e9644ae'
ROUTES = SCRIPTS / 'review_ai_read_route.py'
ROUTES_SHA = '48a1506553804c2b033bbe41d527eca41a9f8b610bed6b32999f6cc89e60053c'
AST_HELPER = SCRIPTS / 'ai_read_postroute_contract.py'
AST_HELPER_SHA = '37f1f50aa55f866d59260a350b25dc0cf9de0e423597bbeb9d65b2e96853fb6b'
READER = 'rtl/hdmi_candidate/hdmi_axi_read.v'
READER_SHA = '7d6779adff9062ab625597534ba18c450b4c830bb7d8808f22fe3952e260650a'
OLD_READER_SHA = '4608af5a4701aa18cdd1513966aae3301909883dc94ea43454bcbc0421f00e17'
NATIVE = REF / 'fpai_demo_vivado.runs/impl_read_v3r9'
SYNTH = REF / 'fpai_demo_vivado.runs/synth_read_v3r9'
SETUP_STAGE = 'read-v3r9-setup-r2'
PREVIEW_RUN = 'synth_read_v3r9_preview_r2'
CACHE_POLICY = 'exact-24-gen-run-xml-mtime-only-v1'
UNUSED_PREVIEW_XML_SHA = '543e62c8b493acf893f51a661ae1508471be17ebb590c7e22bbca5a16f4f0d22'


def need(okay, message):
    if not okay:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ordinary(base, relative):
    path = base / relative
    need(path.resolve().is_relative_to(base.resolve()) and path.is_file() and not path.is_symlink(),
         'Missing/nonordinary protected source: ' + str(path))
    return path


def preparation_identity():
    proof = load(PREPARATION)
    need(proof.get('passed') is True and proof.get('schema') == 'hdmi-reader-boundary-r9-preparation-v1'
         and Path(proof['old_reference']).resolve() == OLD_REF.resolve()
         and Path(proof['new_reference']).resolve() == REF.resolve(), 'Actual independent r7 preparation missing')
    before, after = proof['original_source_sha256'], proof['source_sha256']
    need(len(before) == len(after) == proof['source_count'] == 937 and set(before) == set(after),
         'r7 complete protected source set differs')
    origin = E3 / 'read-v3r3-constraints-r3/review.json'
    need(Path(proof['source_gate_path']).resolve() == origin.resolve()
         and proof['source_gate_SHA256'] == sha(origin) and before == load(origin)['source_sha256'],
         'Original source ledger provenance differs; old report is not a new implementation result')
    need(load(proof['original_source_ledger_path']) == before and load(proof['source_ledger_path']) == after,
         'r7 saved source ledgers differ')
    changed = {name for name in before if before[name] != after[name]}
    moves = proof['path_migrations']
    need(len(moves) == 25 and READER not in moves and changed == set(moves) | {READER},
         'Only 25 exact path migrations and one canonical reader may differ')
    for relative, expected in before.items():
        need(sha(ordinary(OLD_REF, relative)) == expected, 'Original REF changed: ' + relative)
    for relative, expected in after.items():
        current = ordinary(REF, relative)
        need(sha(current) == expected and current.stat().st_nlink == 1
             and not current.samefile(OLD_REF / relative), 'New REF identity/independence changed: ' + relative)
    for relative, move in moves.items():
        raw = (OLD_REF / relative).read_bytes()
        need(move['before_SHA256'] == before[relative] and move['after_SHA256'] == after[relative]
             and move.get('inverse_byte_exact') is True and move['edits'], 'Path migration receipt differs: ' + relative)
        migrated = raw
        last = len(raw) + 1
        for edit in reversed(move['edits']):
            start, end = edit['start'], edit['end']
            old, new = edit['old'].encode('ascii'), edit['new'].encode('ascii')
            need(type(start) is int and type(end) is int and 0 <= start < end < last
                 and raw[start:end] == old and old.lower() == OLD_REF.as_posix().encode().lower()
                 and new == REF.as_posix().encode(), 'Path edit exceeds the exact root substitution: ' + relative)
            migrated = migrated[:start] + new + migrated[end:]
            last = start + 1
        need(migrated == (REF / relative).read_bytes()
             and sha(move['snapshot_before']) == before[relative]
             and sha(move['snapshot_after']) == after[relative], 'Full path-migration bytes differ: ' + relative)
    functional = proof['functional_change']
    need(functional['path'] == READER and functional['before_SHA256'] == before[READER] == OLD_READER_SHA
         and functional['after_SHA256'] == after[READER] == functional['canonical_SHA256'] == READER_SHA
         and sha(functional['canonical_path']) == READER_SHA
         and functional.get('production_repository_or_old_REF_modified') is False,
         'Canonical reader source change differs')
    canonical = load(functional['canonical_name_proof_path'])
    miter = load(functional['miter_result_path'])
    need(sha(functional['canonical_name_proof_path']) == functional['canonical_name_proof_SHA256']
         and canonical.get('all_other_bytes_equal_to_tested_candidate') is True
         and canonical['SHA256'] == READER_SHA
         and sha(functional['miter_result_path']) == functional['miter_result_SHA256']
         and miter.get('passed') is True and miter['strict_output_bits'] == 116 and miter['cases'] == 24
         and miter['cycles'] == 5773 and miter['comparisons'] == 11378,
         'Finite canonical-source miter provenance differs')
    need(proof['old_source_before'] == proof['old_source_after'] == before
         and proof.get('EDA_executed') is False and proof.get('board_executed') is False
         and proof.get('BOOT_or_reboot_authorization') is False, 'Preparation scope/old-source identity differs')
    need(sha(proof['managed_PS_receipt_path']) == proof['managed_PS_receipt_SHA256'], 'Managed PS source receipt changed')
    xpr = proof['xpr']
    old_xpr, new_xpr = OLD_REF / 'fpai_demo_vivado.xpr', REF / 'fpai_demo_vivado.xpr'
    before_xpr = (PREPARATION.parent / 'fpai_demo_vivado.xpr.before').read_bytes()
    after_xpr = (PREPARATION.parent / 'fpai_demo_vivado.xpr.after').read_bytes()
    old_attribute = ('Path="' + old_xpr.as_posix() + '"').encode('ascii')
    new_attribute = ('Path="' + new_xpr.as_posix() + '"').encode('ascii')
    need(sha(old_xpr) == hashlib.sha256(before_xpr).hexdigest() == xpr['before_SHA256']
         and hashlib.sha256(after_xpr).hexdigest() == xpr['after_SHA256']
         and xpr.get('only_Project_Path_changed') is True and xpr.get('inverse_byte_exact') is True
         and xpr['old'] == old_xpr.as_posix() and xpr['new'] == new_xpr.as_posix()
         and xpr['substitution_count'] == 1 and before_xpr.count(old_attribute) == 1
         and after_xpr.count(new_attribute) == 1
         and before_xpr.replace(old_attribute, new_attribute, 1) == after_xpr
         and after_xpr.replace(new_attribute, old_attribute, 1) == before_xpr,
         'Original XPR changed or offline Project.Path-only exact inverse differs')
    safety = load(SAFETY)
    need(safety.get('passed') is True
         and Path(safety['preparation_review_path']).resolve() == PREPARATION.resolve()
         and safety['preparation_review_SHA256'] == sha(PREPARATION)
         and all(safety.get(key) is True for key in [
             'source_preparer_not_rerun', 'old_and_new_no_reparse_or_resolved_escape',
             'all_destinations_nlink1', 'old_copy_file_identities_unchanged',
             'actual_copy_excluded_jobs_by_non_OOC_whitelist',
             'explicit_jobs_and_reparse_checks_added_for_future_use'])
         and safety['ordinary_independent_destination_files'] == 4726
         and len(safety['changed_copy_files']) == 27
         and set(safety['changed_copy_files']) == set(moves) | {READER, 'fpai_demo_vivado.xpr'}
         and safety.get('EDA_executed') is False and safety.get('board_executed') is False,
         'Actual r7 independent-copy safety receipt differs')
    return proof


def installed_identity(proof=None):
    proof = preparation_identity() if proof is None else proof
    ledger = load(INSTALLED)
    need(ledger.get('matching') is True and ledger['checked_files'] == len(ledger['actual']) == 41
         and proof['installed_identity_ledger_SHA256'] == sha(INSTALLED)
         and proof['installed_sha256'] == proof['installed_before'] == proof['installed_after'] == ledger['actual'],
         'r7 original installed-library provenance differs')
    for relative, expected in ledger['actual'].items():
        need(sha(ordinary(TOOL, relative)) == expected, 'Installed tool/library changed: ' + relative)
    return ledger


def stable_sources():
    proof = preparation_identity()
    installed_identity(proof)
    need((REF / 'constrs_1/hdmi_cdc.tcl').read_bytes() == (REF / 'constrs_1/hdmi_cdc.xdc').read_bytes(),
         'HDMI procedural constraint copies differ')
    return proof['source_sha256']


def compare_ooc_cache(before, after, metadata_paths):
    """Only these metadata timestamps may change; no bytes or artifacts may."""
    need(isinstance(metadata_paths, list), 'Cached OOC metadata whitelist must be a path list')
    metadata = sorted(metadata_paths)
    expected_metadata = sorted('fpai_demo_vivado.runs/' + name + '/gen_run.xml'
                               for name in load(PREPARATION)['OOC_cached_run_names'])
    need(len(before) == len(after) == 451 and set(before) == set(after)
         and len(metadata) == len(set(metadata)) == 24 and set(metadata) <= set(before)
         and metadata == expected_metadata
         and all(Path(name).name == 'gen_run.xml' for name in metadata),
         'Cached OOC complete file set/metadata whitelist differs')
    changes = []
    for name in sorted(before):
        old, new = before[name], after[name]
        need(set(old) == set(new) == {'SHA256', 'bytes', 'mtime_ns'}
             and all(isinstance(value['SHA256'], str) and re.fullmatch(r'[0-9a-f]{64}', value['SHA256'])
                     and type(value['bytes']) is int and value['bytes'] >= 0
                     and type(value['mtime_ns']) is int and value['mtime_ns'] >= 0 for value in [old, new])
             and old['SHA256'] == new['SHA256'] and old['bytes'] == new['bytes'],
             'Cached OOC content/size changed: ' + name)
        if old['mtime_ns'] != new['mtime_ns']:
            need(name in metadata, 'Cached OOC nonmetadata timestamp changed: ' + name)
            changes.append(name)
    return {'passed': True, 'policy': CACHE_POLICY, 'files_checked': 451, 'metadata_paths': metadata,
            'allowed_metadata_mtime_changes': changes, 'other_files_mtime_unchanged': 427,
            'all_files_content_and_set_unchanged': True,
            'difference': {'new_files': [], 'deleted_files': [], 'byte_or_size_changed_files': [],
                           'mtime_changed_files': changes}}


def review_unused_preview_xml(original, current):
    """Exact serialization model for one never-executed historical preview.

    These three edits affect only descriptive XML. Every other byte remains
    strict; this is not a generic XML equivalence or ignored-file rule.
    """
    need(type(original) is bytes and type(current) is bytes
         and hashlib.sha256(original).hexdigest() == UNUSED_PREVIEW_XML_SHA,
         'Original unused-preview XML identity differs')
    reports = [
        ('RDS-PROPCONSTRS', 'ai7030_edif_top_drc_synth.rpt'),
        ('RDS-UTIL', 'ai7030_edif_top_utilization_synth.rpt'),
        ('RDS-UTIL-PB', 'ai7030_edif_top_utilization_synth.pb'),
        ('VDS-TIMINGSUMMARY', 'ai7030_edif_top_timing_summary_synth.rpt'),
        ('VDS-TIMING-PB', 'ai7030_edif_top_timing_summary_synth.pb')]
    report_lines = [('  <File Type="' + kind + '" Name="' + name + '"/>\r\n').encode('ascii')
                    for kind, name in reports]
    described = (b'    <StratHandle Name="Vivado Synthesis Defaults" Flow="Vivado Synthesis 2018">\r\n'
                 b'      <Desc>Vivado Synthesis Defaults</Desc>\r\n    </StratHandle>\r\n')
    compact = b'    <StratHandle Name="Vivado Synthesis Defaults" Flow="Vivado Synthesis 2018"/>\r\n'
    pattern = rb'(?m)^  <BlockFileSet Type="BlockSrcs" Name="[^"\r\n]+"/>\r\n'
    original_blocks = re.findall(pattern, original)
    need(len(original_blocks) == len(set(original_blocks)) == 24
         and all(original.count(line) == 1 for line in report_lines)
         and original.count(described) == 1 and original.count(compact) == 0,
         'Fixed unused-preview descriptive model differs')
    source_marker = b'  <FileSet Name="sources" Type="DesignSrcs" RelSrcDir="$PSRCDIR/sources_1">\r\n'
    need(original.count(source_marker) == 1, 'Fixed unused-preview source boundary differs')
    original_header = original[:original.index(source_marker)]
    compact_header = original_header
    for line in report_lines:
        compact_header = compact_header.replace(line, b'', 1)

    def normalized(raw):
        counts = [raw.count(line) for line in report_lines]
        need(counts in [[0] * 5, [1] * 5], 'Unused-preview report descriptors changed beyond the exact five-line group')
        need(raw.startswith(original_header if counts[0] else compact_header),
             'Unused-preview report descriptors moved from their exact original root header')
        value = raw
        for line in report_lines:
            value = value.replace(line, b'', 1)
        state = (value.count(described), value.count(compact))
        need(state in [(1, 0), (0, 1)], 'Unused-preview strategy description/name/flow differs')
        value = value.replace(described, compact, 1)
        blocks = list(re.finditer(pattern, value))
        need(len(blocks) == 24 and sorted(match[0] for match in blocks) == sorted(original_blocks),
             'Unused-preview 24 BlockFileSet raw identities differ')
        start, end = blocks[0].start(), blocks[-1].end()
        need(value[start:end] == b''.join(match[0] for match in blocks)
             and value[end:] == b'</GenRun>\r\n',
             'Unused-preview BlockFileSet block is not contiguous at the original root tail')
        value = value[:start] + b''.join(original_blocks) + value[end:]
        return value, {'five_report_descriptors': 'present' if counts[0] else 'removed',
                       'original_strategy_description': 'present' if state[0] else 'removed',
                       'BlockFileSet_order_changed': [match[0] for match in blocks] != original_blocks}

    def reversible_edits(raw, result):
        left, right = raw.splitlines(keepends=True), result.splitlines(keepends=True)
        left_offsets, right_offsets = [0], [0]
        for line in left:
            left_offsets.append(left_offsets[-1] + len(line))
        for line in right:
            right_offsets.append(right_offsets[-1] + len(line))
        edits = []
        for kind, a, b, c, d in difflib.SequenceMatcher(None, left, right, autojunk=False).get_opcodes():
            if kind != 'equal':
                a, b, c, d = left_offsets[a], left_offsets[b], right_offsets[c], right_offsets[d]
                edits.append({'source_start': a, 'source_end': b, 'result_start': c, 'result_end': d,
                              'old_hex': raw[a:b].hex(), 'new_hex': result[c:d].hex()})
        forward, inverse = raw, result
        for edit in reversed(edits):
            a, b = edit['source_start'], edit['source_end']
            need(forward[a:b].hex() == edit['old_hex'], 'Unused-preview normalization edit source differs')
            forward = forward[:a] + bytes.fromhex(edit['new_hex']) + forward[b:]
            c, d = edit['result_start'], edit['result_end']
            need(inverse[c:d].hex() == edit['new_hex'], 'Unused-preview inverse edit source differs')
            inverse = inverse[:c] + bytes.fromhex(edit['old_hex']) + inverse[d:]
        need(forward == result and inverse == raw, 'Unused-preview normalization exact inverse failed')
        return edits

    before, old_state = normalized(original)
    after, new_state = normalized(current)
    need(before == after, 'Unused-preview root/source/constraint/step/hook or other protected XML bytes changed')
    return {'passed': True, 'model': 'unused-preview1-exact-descriptive-serialization-v1',
            'original_SHA256': hashlib.sha256(original).hexdigest(), 'original_bytes': len(original),
            'current_SHA256': hashlib.sha256(current).hexdigest(), 'current_bytes': len(current),
            'common_normalized_SHA256': hashlib.sha256(before).hexdigest(),
            'original_state': old_state, 'current_state': new_state,
            'normalization_edits': {'original': reversible_edits(original, before),
                                    'current': reversible_edits(current, after)},
            'normalization_inverse_byte_exact': True, 'all_other_bytes_strictly_equal': True,
            'unused_preview_not_synthesis_or_implementation_acceptance': True}


def completed(mode):
    directory = E / (SETUP_STAGE if mode == 'setup' else 'read-v3r9-' + mode)
    execution, phase = load(directory / 'execution.json'), load(directory / 'phase-review.json')
    need(type(execution.get('exit')) is int and execution['exit'] == 0
         and not execution.get('stopped_by_monitor', False) and not execution.get('timeout', False)
         and phase.get('passed') is True and phase.get('mode') == mode
         and phase.get('candidate_run') == 'impl_read_v3r9' and phase.get('managed_run') is True
         and phase.get('parent_synthesis') == 'synth_read_v3r9'
         and phase.get('source_identity_unchanged_after_this_phase') is True
         and 'OOC_cache_bytes_and_mtimes_unchanged' not in phase
         and phase.get('OOC_cache_content_and_set_unchanged') is True
         and phase.get('OOC_cache_nonmetadata_mtimes_unchanged') is True
         and phase.get('OOC_metadata_mtime_policy') == CACHE_POLICY
         and phase.get('managed_PS_OOC_count') == 11 and phase.get('OOC_cached_count') == 24
         and phase.get('extra_r6_postroute_optimization') is False and phase.get('board_executed') is False,
         'Actual r7 phase did not complete with its fixed scope: ' + mode)
    proof, preparation = load(directory / 'input-proof.json'), preparation_identity()
    need(Path(proof['preparation_review_path']).resolve() == PREPARATION.resolve()
         and proof['preparation_review_SHA256'] == sha(PREPARATION)
         and Path(proof['source_safety_review_path']).resolve() == SAFETY.resolve()
         and proof['source_safety_review_SHA256'] == sha(SAFETY)
         and proof['source_sha256'] == preparation['source_sha256']
         and proof['installed_identity_ledger_SHA256'] == sha(INSTALLED)
         and proof['installed_sha256'] == preparation['installed_sha256']
         and proof['original_XPR_SHA256'] == preparation['xpr']['before_SHA256']
         and proof['driver_SHA256'] == sha(directory / 'actual-driver.py') == DRIVER_SHA
         and proof['supervisor_SHA256'] == sha(directory / 'actual-supervisor.py') == SUPERVISOR_SHA
         and proof['managed_PS_receipt_SHA256'] == preparation['managed_PS_receipt_SHA256']
         and proof.get('OOC_cache_policy') == CACHE_POLICY
         and proof.get('extra_r6_postroute_optimization') is False
         and proof.get('new_timing_or_DRC_waiver') is False,
         'Actual r7 phase source/supervisor/preparation chain differs: ' + mode)
    if mode == 'setup':
        snapshot = PREPARATION.parent / 'fpai_demo_vivado.xpr.after'
        need(Path(proof['initial_XPR_source_path']).resolve() == snapshot.resolve()
             and proof['initial_XPR_SHA256'] == sha(snapshot) == preparation['xpr']['after_SHA256']
             and proof.get('fresh_setup_from_independent_clone') is True
             and proof.get('old_failed_r7_setup_or_place_reused') is False,
             'R9 setup must use the exact actual fresh clone')
        original_names = {r.get('Id') for r in ET.parse(snapshot).getroot().iter('Run')}
        need(not original_names.intersection({'synth_read_v3r9', PREVIEW_RUN, 'impl_read_v3r9'}),
             'Fresh clone already contained an R9 top run')
    if mode == 'synthesis':
        setup_snapshot = E / SETUP_STAGE / 'fpai_demo_vivado.xpr'
        need(Path(proof['initial_XPR_source_path']).resolve() == setup_snapshot.resolve()
             and proof['initial_XPR_SHA256'] == sha(setup_snapshot)
             == load(setup_snapshot.with_name('xpr-after-setup.json'))['sha256'],
             'Actual new synthesis did not inherit the exact completed setup-r2 XPR')
    metadata = sorted('fpai_demo_vivado.runs/' + name + '/gen_run.xml'
                      for name in preparation['OOC_cached_run_names'])
    need(proof['OOC_metadata_expected_paths'] == metadata, 'Actual OOC metadata whitelist differs')
    cache = load(directory / 'OOC-cache-after.json')
    need(json.dumps(load(directory / 'OOC-cache-before.json'), sort_keys=True)
         == json.dumps(proof['OOC_cached_files_before'], sort_keys=True),
         'Saved before-cache differs from actual phase input proof')
    comparison = compare_ooc_cache(proof['OOC_cached_files_before'], cache, metadata)
    comparison_path = directory / 'OOC-cache-comparison.json'
    need(json.dumps(load(comparison_path), sort_keys=True) == json.dumps(comparison, sort_keys=True)
         and phase['OOC_cache_comparison_SHA256'] == sha(comparison_path),
         'Actual cached OOC comparison receipt differs')
    for relative in metadata:
        for suffix, inventory in [('before', proof['OOC_cached_files_before']), ('after', cache)]:
            saved = ordinary(directory / ('OOC-metadata-' + suffix), relative)
            need(sha(saved) == inventory[relative]['SHA256']
                 and saved.stat().st_size == inventory[relative]['bytes'],
                 'Actual saved OOC metadata bytes differ: ' + relative)
    current = {}
    for run in preparation['OOC_cached_run_names']:
        base = REF / 'fpai_demo_vivado.runs' / run
        for path in base.rglob('*'):
            need(not path.is_symlink() and path.resolve().is_relative_to(REF.resolve()), 'Cached OOC path escaped REF')
            if path.is_file():
                current[path.relative_to(REF).as_posix()] = {'SHA256': sha(path), 'bytes': path.stat().st_size,
                                                           'mtime_ns': path.stat().st_mtime_ns}
    compare_ooc_cache(cache, current, metadata)
    return {name: sha(directory / name) for name in ['execution.json', 'phase-review.json', 'input-proof.json',
        'actual-driver.py', 'actual-supervisor.py', 'OOC-cache-after.json', 'OOC-cache-comparison.json']}


def setup_xpr_identity():
    preparation = preparation_identity()
    directory = E / SETUP_STAGE
    identity, snapshot = load(directory / 'xpr-after-setup.json'), directory / 'fpai_demo_vivado.xpr'
    need(identity['sha256'] == sha(snapshot)
         and identity['source_preparation_review_sha256'] == sha(PREPARATION)
         and identity['managed_source_review_sha256'] == preparation['managed_PS_receipt_SHA256']
         and identity['PS_output_SHA256'] == sha(REF / 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v'),
         'Actual fresh r7 setup XPR/source identity differs')
    return {'setup_snapshot': str(snapshot), 'setup_SHA256': sha(snapshot),
            'current_SHA256': sha(REF / 'fpai_demo_vivado.xpr'),
            'changed_since_setup': sha(snapshot) != sha(REF / 'fpai_demo_vivado.xpr'),
            'source_preparation_review_SHA256': sha(PREPARATION),
            'scope': 'new actual r7 setup; XPR run-state revisions are recorded separately from RTL'}


def preview_identity():
    """The scripts-only preview is source evidence, never a synthesis pass."""
    setup, synthesis = E / SETUP_STAGE, E / 'read-v3r9-synthesis'
    before_path, after_path = setup / 'preview-native.tcl', synthesis / 'native-script.tcl'
    record = load(setup / 'preview-native-identity.json')
    before, after = before_path.read_bytes(), after_path.read_bytes()
    old, new = PREVIEW_RUN.encode('ascii'), b'synth_read_v3r9'
    positions = [match.start() for match in re.finditer(re.escape(old), before)]
    native_before = REF / ('fpai_demo_vivado.runs/' + PREVIEW_RUN + '/ai7030_edif_top.tcl')
    native_after = SYNTH / 'ai7030_edif_top.tcl'
    need(Path(record['path']).resolve() == native_before.resolve()
         and sha(before_path) == sha(native_before) == record['SHA256']
         and after == native_after.read_bytes() and positions
         and before.count(new) == after.count(new) == len(positions)
         and before.replace(old, new) == after and after.replace(new, old) == before,
         'Actual native synthesis differs beyond the reviewed preview run-name substitution')
    equivalence = load(synthesis / 'preview-actual-equivalence.json')
    expected = {'passed': True, 'preview_path': str(before_path), 'preview_SHA256': sha(before_path),
                'actual_path': str(native_after), 'actual_SHA256': sha(native_after),
                'old_run': old.decode(), 'new_run': new.decode(), 'substitution_count': len(positions),
                'old_positions': positions, 'inverse_byte_exact': True,
                'preview_scripts_only_not_synthesis_pass': True}
    need(equivalence == expected, 'Actual synthesis preview inverse receipt differs')
    stage = (setup / 'stage.tcl').read_text()
    need(re.findall(r'^\s*launch_runs\s+([^\r\n]+)', stage, re.MULTILINE)
         == [PREVIEW_RUN + ' -scripts_only']
         and not re.search(r'^\s*(?:reset_run|reset_runs)\b', stage, re.MULTILINE)
         and not (native_before.parent / '.synth_design.end.rst').exists()
         and not (native_before.parent / 'runme.log').exists(),
         'Setup preview was executed/reset rather than source-only preparation')
    bd_line = ('add_files ' + (REF / 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd').as_posix()).lower()
    for raw in [before, after]:
        need([line.strip().lower() for line in raw.decode().replace('\\', '/').splitlines()].count(bd_line) == 1,
             'Reviewed preview/actual native does not add the original managed BD uniquely')
    return {'preview_scripts_only_not_synthesis_pass': True,
            'preview_actual_inverse': equivalence,
            'preview_status_SHA256': sha(setup / 'preview-run-status.txt'),
            'equivalence_receipt_SHA256': sha(synthesis / 'preview-actual-equivalence.json')}


def frozen_module(path, expected, changes=()):
    need(sha(AST_HELPER) == AST_HELPER_SHA, 'Frozen shared AST adapter changed')
    spec = importlib.util.spec_from_file_location('r7_frozen_AST_adapter', AST_HELPER)
    adapter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(adapter)
    _, proof, _, adapted = adapter.adapt_frozen(path, expected, list(changes), Path(__file__))
    module = ModuleType('r7_shared_fixed_algorithms')
    module.__file__ = str(path)
    exec(compile(adapted, str(path) + ' [r7 explicit identities]', 'exec'), vars(module))
    return module, proof


def constraints_algorithms():
    tree = ast.parse(CONSTRAINTS.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    edits = [(node.lineno, node.col_offset, 'review.json', 'common-constraints-review.json')
             for node in ast.walk(main) if isinstance(node, ast.Constant) and node.value == 'review.json']
    need(len(edits) == 2, 'Frozen constraints output locations differ')
    module, proof = frozen_module(CONSTRAINTS, CONSTRAINTS_SHA, edits)
    managed, _ = frozen_module(CONSTRAINTS, CONSTRAINTS_SHA)
    # Public configuration: source proof keeps its historical evidence root,
    # while every actual report/setup/native dependency uses the new r7 root.
    managed.REFERENCE = REF
    module.E3, module.REFERENCE = E, REF
    module.SETUP_STAGE, module.BUILD_PREFIX = SETUP_STAGE, 'read-v3r9-'
    module.CONSTRAINT_STAGE, module.SYNTH_RUN = 'read-v3r9-constraints', 'synth_read_v3r9'
    module.completed = lambda stage: completed('setup' if stage == SETUP_STAGE else stage.removeprefix('read-v3r9-'))
    module.stable_sources = stable_sources
    module.setup_xpr_identity = setup_xpr_identity
    module.managed_ps_identity = managed.managed_ps_identity
    return module, proof


def checkpoint_identity(path):
    need(path.is_file() and path.stat().st_size > 0, 'Actual checkpoint missing: ' + str(path))
    return {'path': str(path), 'bytes': path.stat().st_size, 'SHA256': sha(path)}


def phase_artifacts(mode, native_checkpoint):
    directory = E / ('read-v3r9-' + mode)
    artifacts = load(directory / 'phase-artifacts.json')
    exported = load(directory / 'checkpoint-identity.json')
    need(artifacts.get('mode') == mode and artifacts.get('candidate_run') == 'impl_read_v3r9'
         and artifacts.get('parent_synthesis') == 'synth_read_v3r9' and artifacts.get('managed_run') is True
         and artifacts['checkpoint'] == exported
         and exported == checkpoint_identity(Path(exported['path']))
         and Path(exported['path']).resolve().is_relative_to(directory.resolve())
         and artifacts['native_checkpoint'] == checkpoint_identity(native_checkpoint),
         'Actual new exported/native checkpoint identities differ: ' + mode)
    native = artifacts['native']
    frozen = directory / 'native-script.tcl'
    need(sha(frozen) == native['SHA256'] and native.get('only_new_REF_or_fixed_toolchain') is True,
         'Actual native script source identity differs: ' + mode)
    return artifacts


def synthesis_native_completion(native, stage):
    """Actual 2018.3 project-run markers; never a substitute for the other gates."""
    required = ['__synthesis_is_complete__', '.vivado.begin.rst', '.vivado.end.rst']
    need(all((native / name).is_file() and not (native / name).is_symlink() for name in required)
         and (native / '__synthesis_is_complete__').stat().st_size == 0
         and (native / '.vivado.end.rst').stat().st_size == 0
         and (native / '.vivado.begin.rst').stat().st_size > 0
         and not any((native / name).exists() for name in [
             '__synthesis_is_running__', '.vivado.error.rst', '.synth_design.error.rst']),
         'Actual fresh r7 native synthesis markers missing/running/error')
    script = native / 'ai7030_edif_top.tcl'
    lines = script.read_text().splitlines()
    commands = ['close [open __synthesis_is_running__ w]',
                'synth_design -top ai7030_edif_top -part xc7z030ffg676-2',
                'write_checkpoint -force -noxdef ai7030_edif_top.dcp',
                'file delete __synthesis_is_running__', 'close [open __synthesis_is_complete__ w]']
    need(all(lines.count(command) == 1 for command in commands), 'Actual native synthesis marker/command identities differ')
    positions = [lines.index(command) for command in commands]
    need(positions == sorted(positions), 'Actual native synthesis completion does not follow synthesis/checkpoint')
    stage_path = stage / 'stage.tcl'
    stage_lines = stage_path.read_text().splitlines()
    status = 'if {[get_property STATUS $nr] ne "synth_design Complete!" || [get_property NEEDS_REFRESH $nr]} {error "Fresh synthesis incomplete/stale"}'
    need(stage_lines.count(status) == 1 and stage_lines.count('wait_on_run synth_read_v3r9') == 1
         and stage_lines.count('open_run synth_read_v3r9') == 1
         and stage_lines.index('wait_on_run synth_read_v3r9') < stage_lines.index(status)
         < stage_lines.index('open_run synth_read_v3r9'), 'Existing actual top-run status/refresh assertion differs')
    return {'native_marker_SHA256': {name: sha(native / name) for name in required},
            'native_script_SHA256': sha(script), 'native_command_lines': dict(zip(commands, [i+1 for i in positions])),
            'actual_stage_SHA256': sha(stage_path), 'status_assertion_line': stage_lines.index(status)+1,
            'running_or_error_marker_present': False,
            'scope': 'native completion identity only; actual exit/log/DCP/source/preview and all later gates remain required'}


def verify_synthesis():
    phases = {mode: completed(mode) for mode in ['setup', 'synthesis']}
    completion = synthesis_native_completion(SYNTH, E / 'read-v3r9-synthesis')
    log = SYNTH / 'runme.log'
    text = log.read_text()
    need('synth_design completed successfully' in text and not re.search(r'^ERROR:', text, re.MULTILINE),
         'Actual native r7 synthesis failed/incomplete')
    old_log = OLD_REF / 'fpai_demo_vivado.runs/synth_read_v3r3/runme.log'
    need(sha(old_log) == '1d7619c85b332244a82bf39fdda944e4b69a1924b47bb6710672dc299a43c892',
         'Original critical-warning source ledger changed')
    normalize = lambda line: line.replace('\\', '/').replace(REF.as_posix(), '@@REF@@').replace(OLD_REF.as_posix(), '@@REF@@')
    critical = [normalize(line) for line in text.splitlines() if line.startswith('CRITICAL WARNING:')]
    old_critical = [normalize(line) for line in old_log.read_text().splitlines() if line.startswith('CRITICAL WARNING:')]
    environment_note = "CRITICAL WARNING: [Common 17-741] No write access right to the local Tcl store at 'C'. XilinxTclStore is reverted to the installation area. If you want to use local Tcl Store, please change the access right and relaunch Vivado."
    need(len(critical) == 16 and critical.count(environment_note) == 1
         and len(old_critical) == 15 and [x for x in critical if x != environment_note] == old_critical,
         'R9 warning delta differs from the explicitly reviewed single startup-store warning')
    helper, _ = constraints_algorithms()
    dependencies = helper.compile_dependency_identity()
    artifacts = phase_artifacts('synthesis', SYNTH / 'ai7030_edif_top.dcp')
    return {'passed': True, 'candidate_run': 'synth_read_v3r9', 'actual_phase_identity_SHA256': phases,
            'source_preparation_review_SHA256': sha(PREPARATION), 'source_sha256': stable_sources(),
            'installed_library_identity': installed_identity(), 'managed_PS_source_identity': helper.managed_ps_identity(),
            'actual_managed_PS_compile_dependencies': dependencies, 'setup_XPR_identity': setup_xpr_identity(),
            'preview_native_equivalence': preview_identity(),
            'synthesis_checkpoint': checkpoint_identity(SYNTH / 'ai7030_edif_top.dcp'),
            'actual_artifacts': artifacts,
            'actual_native_completion': completion,
            'native_log_SHA256': sha(log), 'native_critical_warnings': critical,
            'additional_environment_warning': environment_note, 'original_15_critical_warnings_identical': True,
            'ordinary_warnings_retained_not_asserted_identical': True,
            'new_timing_or_DRC_waiver': False, 'new_BOOT_or_reboot_authorized': False}


def verify_fullflow():
    proof = preparation_identity()
    phases = {mode: completed(mode) for mode in ['setup', 'synthesis', 'constraints', 'place', 'route', 'reports']}
    synthesis = verify_synthesis()
    gate_path = E / 'read-v3r9-constraints/review.json'
    gate = load(gate_path)
    need(gate.get('route_prerequisite_pass') is True and gate.get('candidate_run') == 'impl_read_v3r9'
         and gate.get('read_bits') == 2768 and gate['source_sha256'] == proof['source_sha256']
         and gate['source_preparation_review_SHA256'] == sha(PREPARATION)
         and gate.get('r9_contract_SHA256') == sha(Path(__file__))
         and gate.get('actual_adapter_SHA256') == sha(SCRIPTS / 'review_ai_read_r9_constraints.py')
         and gate.get('review_driver_SHA256') == CONSTRAINTS_SHA, 'Actual new r7 constraint gate differs')
    need(gate['managed_PS_source_identity'] == synthesis['managed_PS_source_identity']
         and gate['actual_managed_PS_compile_dependencies'] == synthesis['actual_managed_PS_compile_dependencies'],
         'New managed PS source/dependency identity changed after the actual r7 constraints gate')
    need((NATIVE / '.route_design.end.rst').is_file()
         and not (NATIVE / '.route_design.error.rst').exists(), 'Actual fresh r7 route completion absent')
    # launch_runs may rewrite a native script for its next step; each actual
    # phase therefore retains its own complete source instead of borrowing r3/r6.
    place_script = E / 'read-v3r9-place/native-script.tcl'
    route_script = E / 'read-v3r9-route/native-script.tcl'
    place_text, route_text = place_script.read_text().replace('\\', '/'), route_script.read_text().replace('\\', '/')
    synth_line = 'add_files -quiet ' + (SYNTH / 'ai7030_edif_top.dcp').as_posix()
    need(sum(line.strip() == synth_line for line in place_text.splitlines()) == 1,
         'Fresh physical implementation did not consume the actual new r7 synthesis')
    bd_line = 'add_files ' + (REF / 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd').as_posix()
    need(sum(line.strip() == bd_line for line in place_text.splitlines()) == 1,
         'Fresh implementation lacks its unique original managed BD source')
    profile_rows = (E / 'read-v3r9-place/implementation-profile.txt').read_text().splitlines()
    profile = dict(line.split('|', 1) for line in profile_rows)
    required = {'STRATEGY': 'Performance_NetDelay_high', 'CONSTRSET': 'constrs_1',
                'PART': 'xc7z030ffg676-2', 'STEPS.PLACE_DESIGN.ARGS.DIRECTIVE': 'ExtraNetDelay_high',
                'STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE': 'AggressiveExplore',
                'STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE': 'NoTimingRelaxation'}
    need(all(profile.get(key) == value for key, value in required.items())
         and profile.get('STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED', '').lower() in {'0', 'false'},
         'Actual new r7 original implementation strategy/profile differs')
    for key, relative in {
        'STEPS.OPT_DESIGN.TCL.PRE': 'implementation_opt_pre_hdmi.tcl',
        'STEPS.OPT_DESIGN.TCL.POST': 'implementation_opt_post.tcl',
        'STEPS.ROUTE_DESIGN.TCL.POST': 'implementation_route_post.tcl',
        'STEPS.WRITE_BITSTREAM.TCL.PRE': 'write_bitstream_pre.tcl',
        'STEPS.WRITE_BITSTREAM.TCL.POST': 'write_bitstream_post.tcl'}.items():
        need(Path(profile.get(key, '')).resolve() == (REF / 'ip_patch/process_control' / relative).resolve(),
             'Original complete factory hook binding differs: ' + key)
    for mode, run in [('constraints', 'synth_read_v3r9'), ('reports', 'impl_read_v3r9')]:
        stage_text = (E / ('read-v3r9-' + mode) / 'stage.tcl').read_text()
        need(stage_text.count('open_project {' + (REF / 'fpai_demo_vivado.xpr').as_posix() + '}') == 1
             and len(re.findall(r'^\s*open_run ' + run + r'\s*$', stage_text, re.MULTILINE)) == 1,
             'Actual new r7 report/constraint phase consumed a different run: ' + mode)
    physical = checkpoint_identity(NATIVE / 'ai7030_edif_top_physopt.dcp')
    routed = checkpoint_identity(NATIVE / 'ai7030_edif_top_routed.dcp')
    place_receipt = phase_artifacts('place', NATIVE / 'ai7030_edif_top_physopt.dcp')
    route_receipt = phase_artifacts('route', NATIVE / 'ai7030_edif_top_routed.dcp')
    need(place_receipt['parent_checkpoint'] == synthesis['synthesis_checkpoint']
         and route_receipt['parent_checkpoint'] == physical,
         'Actual fresh synth/place/route checkpoint lineage differs')
    for text in [place_text, route_text]:
        need('phys_opt_design -placement_opt -routing_opt -rewire -critical_pin_opt' not in text
             and 'R6_POSTROUTE_PHYSICAL_EXPERIMENT' not in text, 'r7 must not inherit the r6 optimizer trial')
    route_calls = [line.strip() for line in route_text.splitlines() if re.match(r'^\s*route_design\b', line)]
    need(route_calls == ['route_design -directive NoTimingRelaxation'], 'r7 routing strategy/pass count differs')
    need(len(re.findall(r'^\s*source\s+[^\n]*implementation_route_post\.tcl[^\n]*$', route_text, re.MULTILINE)) == 1,
         'Actual r7 route must call the complete original factory hook once')
    return {'candidate_run': 'impl_read_v3r9', 'managed_run': True,
            'source_preparation_review_SHA256': sha(PREPARATION),
            'actual_phase_identity_evidence_SHA256': phases, 'synthesis_checkpoint': synthesis['synthesis_checkpoint'],
            'physical_checkpoint': physical, 'routed_checkpoint': routed,
            'actual_native_scripts': {str(place_script): sha(place_script), str(route_script): sha(route_script)},
            'old_r3_r6_checkpoint_or_pass_reused': False, 'r6_postroute_optimization_inherited': False,
            'new_timing_or_DRC_waiver': False}


def routed_report_algorithm():
    """Reuse only the exact fixed report body, without old checkpoint lineage."""
    module, _ = frozen_module(ROUTES, ROUTES_SHA)
    tree = ast.parse(ROUTES.read_bytes())
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    assigns = lambda node, name: isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)
    start = next(i for i, node in enumerate(main.body) if assigns(node, 'timing'))
    end = next(i for i, node in enumerate(main.body) if assigns(node, 'review'))
    original = copy.deepcopy(main.body[start:end + 1])
    body = copy.deepcopy(original)
    result = body[-1].value
    need(isinstance(result, ast.Dict), 'Frozen routed report result changed')
    omitted = {}
    for index in reversed(range(len(result.keys))):
        key = result.keys[index]
        if isinstance(key, ast.Constant) and key.value in {'candidate_run', 'managed_run', 'checkpoint_continuation'}:
            omitted[index] = (result.keys.pop(index), result.values.pop(index))
    need(len(omitted) == 3, 'Frozen checkpoint-only result identities changed')
    restored = copy.deepcopy(body)
    for index, pair in sorted(omitted.items()):
        restored[-1].value.keys.insert(index, copy.deepcopy(pair[0]))
        restored[-1].value.values.insert(index, copy.deepcopy(pair[1]))
    need(ast.dump(ast.Module(restored, []), include_attributes=False)
         == ast.dump(ast.Module(original, []), include_attributes=False), 'Routed report body inverse differs')
    args = ['directory', 'native', 'gate', 'helper', 'sources', 'installed_path', 'installed', 'proof_hashes', 'helpers_path']
    fn = ast.FunctionDef(name='evaluate_r7_routed_reports', args=ast.arguments(posonlyargs=[],
        args=[ast.arg(arg=name) for name in args], kwonlyargs=[], kw_defaults=[], defaults=[]),
        body=body + [ast.Return(ast.Name('review', ast.Load()))], decorator_list=[])
    generated = ast.fix_missing_locations(ast.Module([fn], []))
    exec(compile(generated, str(ROUTES) + ' [unchanged r7 report body]', 'exec'), vars(module))
    proof = {'base_source_SHA256': ROUTES_SHA, 'original_statement_count': len(original),
             'only_checkpoint_result_identity_keys_omitted': ['candidate_run', 'managed_run', 'checkpoint_continuation'],
             'inverse_complete_retained_report_AST_equal': True,
             'old_checkpoint_and_old_pass_preamble_executed': False}
    return module.evaluate_r7_routed_reports, proof
