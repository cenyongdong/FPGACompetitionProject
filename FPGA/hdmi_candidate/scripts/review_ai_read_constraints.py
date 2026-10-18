"""Review actual r3 constraints/CDC/clock reports; never launches EDA or a device.

The optimized read-bank width is discovered from actual indices. Every CDC
payload row and every timed capture endpoint must cover exactly those indices.
This gate does not prove physical CDC safety, whole-design equivalence or board
behavior; the two original AI timing-model exceptions are not expanded here.
"""
from pathlib import Path
import collections
import hashlib
import json
import math
import re

ROOT = Path(__file__).resolve().parents[3]
E3 = ROOT / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REFERENCE = ROOT / '.local/hdmi-live-20261017-r3/reference'
READ_SCOPE = 'U0_ps_ai_peripheral/ai_read_path_monitor/'
OLD_SCOPE = 'U0_ps_ai_peripheral/ai_path_monitor/'
SETUP_STAGE = 'read-v3r2-setup'
BUILD_PREFIX = 'read-v3r3-'
CONSTRAINT_STAGE = 'read-v3r3-constraints-r3'
SYNTH_RUN = 'synth_read_v3r3'
PS_REL = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v'
WRAPPER_REL = 'rtl/ps_ai_wrapper.sv'
BD_REL = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
MANAGED_RECEIPT = E3 / 'managed-PS-observer-r2/review.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def completed(stage):
    require(load(E3 / stage / 'execution.json')['exit'] == 0, f'actual EDA stage failed: {stage}')


def cdc_rows(path):
    text = path.read_text()
    rows = [line for line in text.splitlines() if re.match(r'^\s*\d+\s+CDC-\d+\s', line)]
    require(rows, f'no detailed CDC rows: {path.name}')
    return rows


def monitor_cdc(path, scope, expected_indices, read_monitor):
    rows = cdc_rows(path)
    counts = dict(collections.Counter(re.search(r'CDC-\d+', line)[0] for line in rows))
    expected_counts = {'CDC-3': 4 if read_monitor else 2, 'CDC-9': 2, 'CDC-15': len(expected_indices)}
    require(counts == expected_counts, f'{path.name} unexpected CDC rows: {counts}/{expected_counts}')
    require(not any('Critical' in line for line in rows), f'{path.name} has Critical crossing')
    payload_source, payload_capture = [], []
    toggles, resets = set(), set()
    names = ['arm_request', 'freeze_request', 'arm_ack', 'freeze_ack'] if read_monitor else ['request', 'ack']
    for line in rows:
        kind = re.search(r'CDC-\d+', line)[0]
        if kind == 'CDC-15':
            require('Max Delay Datapath Only' in line, 'payload lacks datapath-only max delay')
            source = re.search(re.escape(scope) + r'source_snapshot_reg\[(\d+)\]/C\b', line)
            target = re.search(re.escape(scope) + r'csr_snapshot_reg\[(\d+)\]/D\b', line)
            require(source is not None and target is not None, 'unexpected payload endpoints')
            source_index, target_index = int(source[1]), int(target[1])
            require(source_index == target_index, 'payload CDC source/capture bit mismatch')
            payload_source.append(source_index)
            payload_capture.append(target_index)
        elif kind == 'CDC-3':
            require('False Path' in line and 'Depth' not in line and 'ASYNC_REG' in line,
                    'unexpected synchronizer structure/exception')
            found = [name for name in names if scope + name + '_toggle_reg/C' in line
                     and scope + name + '_sync_reg[0]/D' in line]
            require(len(found) == 1 and found[0] not in toggles, 'unrecognized/duplicate first-stage toggle')
            toggles.add(found[0])
        else:
            require('False Path' in line and 'ASYNC_REG' in line, 'unexpected reset CDC structure')
            found = [name for name in ['source_release', 'csr_release'] if scope + name + '_reg[0]/CLR' in line]
            require(len(found) == 1 and found[0] not in resets, 'unrecognized/duplicate reset first CLR')
            resets.add(found[0])
    require(toggles == set(names) and resets == {'source_release', 'csr_release'}, 'CDC handshake/reset set incomplete')
    require(sorted(payload_source) == sorted(expected_indices) == sorted(payload_capture),
            'CDC payload indices missing/duplicate/not matched to actual registers')
    return {'row_counts': counts, 'payload_indices': sorted(payload_capture),
            'first_stage_toggles': sorted(toggles), 'reset_release_chains': sorted(resets),
            'unknown_or_Critical_rows': 0, 'raw_async_metadata_crossing_accepted': False}


def parse_indices(text, source_key='source_indices', capture_key='capture_indices'):
    parsed = []
    for name in [source_key, capture_key]:
        matches = re.findall(r'^' + re.escape(name) + r'=([^\r\n]+)', text, re.MULTILINE)
        require(len(matches) == 1 and re.fullmatch(r'[\d\s]+', matches[0]), f'actual {name} list missing/malformed')
        values = [int(item) for item in matches[0].split()]
        require(values and values == sorted(set(values)) and values[-1] < 3328, f'invalid {name} indices')
        parsed.append(values)
    require(parsed[0] == parsed[1], 'actual source/capture index sets differ')
    return parsed[0]


def snapshot_endpoints(path, expected_indices):
    rows = [line for line in path.read_text().splitlines() if line.strip()]
    covered, records = [], []
    for line in rows:
        parts = line.split('|')
        endpoint = re.fullmatch(re.escape(READ_SCOPE) + r'csr_snapshot_reg\[(\d+)\]/D', parts[0])
        require(endpoint is not None, f'unexpected read snapshot endpoint: {line}')
        fields = dict(item.split('=', 1) for item in parts[1:] if '=' in item)
        require('requirement' in fields and 'slack' in fields, f'endpoint timing missing: {line}')
        requirement, slack = float(fields['requirement']), float(fields['slack'])
        require(math.isfinite(requirement) and math.isfinite(slack)
                and abs(requirement - 10.0) <= 0.001 and slack >= 0, f'endpoint timing failed: {line}')
        covered.append(int(endpoint[1]))
        records.append({'index': int(endpoint[1]), 'requirement_ns': requirement, 'slack_ns': slack})
    require(sorted(covered) == sorted(expected_indices), 'read snapshot timed endpoints missing/duplicate')
    return {'covered_bits': len(covered), 'minimum_slack_ns': min(x['slack_ns'] for x in records),
            'all_requirements_ns': 10.0, 'records': records}


def clock_taps(path, expected_indices=None):
    text = path.read_text()
    require('AI_READ_CLOCK_REVIEW_FAILED' not in text and text.count('AI_READ_CLOCK_REVIEW_PASS|') == 1,
            'actual clock-tap gate failed/incomplete')
    clocks, groups, coverage, pins = {}, {}, {}, collections.defaultdict(list)
    segments, shared, pass_fields = [], [], None
    def fields(parts):
        values = [part.split('=', 1) for part in parts if '=' in part]
        require(len(values) == len({item[0] for item in values}), 'duplicate clock report field')
        return dict(values)
    for line in text.splitlines():
        parts = line.split('|')
        if parts[0] in ['CLOCK', 'GROUP', 'COVERAGE']:
            table = {'CLOCK': clocks, 'GROUP': groups, 'COVERAGE': coverage}[parts[0]]
            require(parts[1] not in table, 'duplicate clock group record: ' + line)
            table[parts[1]] = fields(parts[2:])
        elif parts[0] == 'CLOCK_PIN':
            pins[parts[1]].append(fields(parts[2:]))
        elif parts[0] == 'SOURCE_NET_SEGMENT':
            segments.append(fields(parts[1:])['net'])
        elif parts[0] == 'SOURCE_NET_SHARED':
            shared.append(fields(parts[1:]))
        elif parts[0] == 'AI_READ_CLOCK_REVIEW_PASS':
            pass_fields = fields(parts[1:])
    base = 'U0_ps_ai_peripheral/'
    monitor = base + 'ai_read_path_monitor/'
    hc = base + 'ZGolo/u_AI_Mate_top/U0_ddr2hp_itcn/'
    ps = base + 'ps_ai_wrapper_u0/ps_ai_i/'
    patterns = {
        'source_snapshot': re.escape(monitor) + r'source_snapshot_reg\[(\d+)\]/C',
        'csr_snapshot': re.escape(monitor) + r'csr_snapshot_reg\[(\d+)\]/C',
        'live_counter_registers': re.escape(monitor) + r'live_words_reg[^/]+/C',
        'monitor_source_control': re.escape(monitor) + r'(?:source_release_reg|arm_request_sync_reg|freeze_request_sync_reg|arm_ack_toggle_reg|freeze_ack_toggle_reg|source_active_reg)[^/]*/C',
        'HC_round_robin': re.escape(hc + 'U0_dmux4/') + r'.+/C',
        'HC1_internal_join': re.escape(base + 'ZGolo/u_AI_Mate_top/u_axi_2to1/') + r'.+/C',
        'HP2_crossbar': re.escape(ps + 'axi_interconnect_4/xbar/') + r'.+/C',
        'HP2_reset_controller': re.escape(ps + 'proc_sys_reset_1/') + r'.+/C',
        'HDMI_AXI_reader': re.escape(base + 'hdmi_display/scanout/core/core/reader/') + r'.+/C',
        'PS7_SAXIHP2ACLK': re.escape(ps + 'processing_system7_0/inst/PS7_i/PS7_inst/SAXIHP2ACLK')}
    for lane in range(4):
        patterns[f'HC{lane}_mna_converter'] = re.escape(hc + f'U{lane}_mna_to_axi_burst/') + r'.+/C'
        patterns[f'HC{lane}_narrow_to_wide'] = re.escape(hc + f'U{lane}_n2w_bwc_r/') + r'.+/C'
    for name in ['s00', 's01', 'm00']:
        patterns[f'HP2_{name}_coupler'] = re.escape(ps + f'axi_interconnect_4/{name}_couplers/') + r'.+/C'
    labels = set(patterns)
    require(set(clocks) == set(groups) == set(coverage) == set(pins) == labels,
            'actual mandatory FF/PS7 clock groups incomplete/unrecognized')
    source_clock = clocks['source_snapshot']['clock']
    csr_clock = clocks['csr_snapshot']['clock']
    require(source_clock and csr_clock and source_clock != csr_clock, 'CSR/source clock objects not distinct')
    all_pins, pin_sets, summaries = [], {}, {}
    for label in sorted(labels):
        clock = clocks[label]
        actual = pins[label]
        names = [item['pin'] for item in actual]
        minimum = 1024 if label in ['source_snapshot', 'csr_snapshot', 'live_counter_registers'] else 10 if label == 'monitor_source_control' else 1
        require(len(names) >= minimum and len(names) == len(set(names)), f'clock group empty/duplicate/short: {label}')
        require(int(clock['pins']) == int(groups[label]['cells']) == int(groups[label]['pins']) == len(names),
                f'clock group member/count coverage differs: {label}')
        expected_kind = 'PS7' if label == 'PS7_SAXIHP2ACLK' else 'FF_C'
        require(groups[label]['kind'] == expected_kind, f'actual clock pin kind wrong: {label}')
        for key in ['enumerated_cells', 'queried_pins', 'unique_pins', 'clocked_pins']:
            require(int(coverage[label][key]) == len(names), f'per-pin clock coverage missing: {label}/{key}')
        for key in ['unclocked_pins', 'multi_clock_pins', 'wrong_clock_pins']:
            require(int(coverage[label][key]) == 0, f'per-pin clock failure: {label}/{key}')
        expected_clock = csr_clock if label == 'csr_snapshot' else source_clock
        expected_period = 10. if label == 'csr_snapshot' else 5.
        require(clock['clock'] == expected_clock and math.isfinite(float(clock['period_ns']))
                and abs(float(clock['period_ns'])-expected_period) <= .001,
                f'clock object/period contract failed: {label}')
        for item in actual:
            require(re.fullmatch(patterns[label], item['pin']) is not None,
                    f'wrong actual clock pin group membership: {label}/{item["pin"]}')
            require(item['ref'] == 'PS7' if label == 'PS7_SAXIHP2ACLK' else item['ref'].startswith('FD'),
                    f'actual clock pin not FF/PS7: {label}')
            require(item['clock'] == expected_clock and math.isfinite(float(item['period_ns']))
                    and abs(float(item['period_ns'])-expected_period) <= .001,
                    f'per-pin clock object/period differs: {label}/{item["pin"]}')
        if label == 'PS7_SAXIHP2ACLK':
            require(len(names) == 1, 'real PS7 HP2 clock not unique')
        pin_sets[label] = set(names)
        all_pins.extend(names)
        summaries[label] = {'pins': len(names), 'clock': expected_clock, 'period_ns': expected_period,
                            'all_actual_pins_clocked_once': True}
    require(len(all_pins) == len(set(all_pins)), 'same actual clock pin counted in different mandatory groups')
    snapshot_indices = []
    for label in ['source_snapshot', 'csr_snapshot']:
        snapshot_indices.append(sorted(int(re.fullmatch(patterns[label], name)[1]) for name in pin_sets[label]))
    require(snapshot_indices[0] == snapshot_indices[1], 'clock-tap snapshot source/capture index mismatch')
    if expected_indices is not None:
        require(snapshot_indices[0] == sorted(expected_indices), 'clock-tap snapshot coverage differs from binding/CDC')
    require(len(shared) == 1 and len(segments) == len(set(segments)) > 0, 'shared physical clock-net record incomplete')
    net = shared[0]
    mig_net = base + 'mig_ddr3_u0/u_mig_7series_0_mig/u_ddr3_infrastructure/CLK'
    require(int(net['same_segment_count']) == len(segments) and net['MIG_UI_net'] == mig_net
            and mig_net in segments and net['source_snapshot_C'] in pin_sets['source_snapshot']
            and net['PS7_HP2_C'] in pin_sets['PS7_SAXIHP2ACLK'],
            'MIG/source-snapshot/PS7 physical clock-net provenance mismatch')
    require(pass_fields['same_source_clock'] == source_clock and pass_fields['csr_clock'] == csr_clock
            and float(pass_fields['source_period']) == 5. and float(pass_fields['csr_period']) == 10.
            and 'every_group_pin_clock_checked' in text, 'final actual clock review contract incomplete')
    require(all(marker in text for marker in ['RESET_CHAIN_NOTE|', 'EXCLUDED_CONSTANT_PORTS|',
            'OPTIMIZED_PORTS_NOTE|', 'RESET_DETAIL|observer_source_release|',
            'RESET_DETAIL|observer_csr_release|', 'RESET_DETAIL|HP2_controller_register_reset_inputs|']),
            'reset/constant/optimized-port interpretation missing')
    return {'passed': True, 'source_clock': source_clock, 'source_period_ns': 5.,
            'csr_clock': csr_clock, 'csr_period_ns': 10., 'clock_groups_checked': len(clocks),
            'actual_pin_records_checked': len(all_pins), 'group_coverage': summaries,
            'clock_report_SHA256': digest(path), 'shared_MIG_UI_PS7_net_segments': len(segments),
            'different_reset_chains_not_equated': True, 'optimized_boundary_ports_used_as_evidence': False}


def setup_xpr_identity():
    directory = E3 / SETUP_STAGE
    identity_path = directory / 'xpr-after-setup.json'
    original_path = directory / 'fpai_demo_vivado.xpr'
    identity = load(identity_path)
    expected = identity.get('sha256', identity.get('SHA256'))
    require(isinstance(expected, str) and digest(original_path) == expected, 'setup XPR snapshot identity failed')
    require(identity['managed_source_review_sha256'] == digest(MANAGED_RECEIPT),
            'setup XPR was not bound to this managed PS receipt')
    require(identity['PS_output_SHA256'] == digest(REFERENCE / PS_REL),
            'managed PS output changed since setup')
    current = digest(REFERENCE / 'fpai_demo_vivado.xpr')
    return {'setup_snapshot': str(original_path), 'setup_SHA256': expected,
            'current_SHA256': current, 'changed_since_setup': current != expected,
            'scope': 'full XPR identities retained separately; run-state revisions are not RTL changes'}


def managed_ps_identity():
    """Check actual full managed output against exact saved top-only edits."""
    directory = MANAGED_RECEIPT.parent
    receipt = load(MANAGED_RECEIPT)
    require(receipt['passed'] and receipt['full_original_byte_exact_reconstruction']
            and receipt['other_12_original_modules_byte_identical']
            and receipt['original_timescale_unchanged']
            and receipt['BD_XCI_or_OOC_content_changed'] is False,
            'managed PS source restoration proof failed')
    require(set(receipt['changes']) == {PS_REL, WRAPPER_REL}, 'managed receipt changes exceed PS/wrapper scope')
    bound = {
        PS_REL: ('b253cc32badb6bc182e3dfce3e5732b43229d6d93ca07e2d98b582783700a5e2',
                 'b87b798ce01c707027766660c501ed2232aaeaec5f093bc291e095ab1f637cb7'),
        WRAPPER_REL: ('41d38c173b050ac8a9cb80818dc890fc1df763cbec376f92f2928c764056ab37',
                      '502c463544a5cbc4e5af20460af274418e5f6c68661e92ee6a3eca9c8b3c86f2')}
    for rel, (before_hash, after_hash) in bound.items():
        change = receipt['changes'][rel]
        require(change == {'before': before_hash, 'after': after_hash}, f'unreviewed managed change: {rel}')
        for suffix, value in [('before', before_hash), ('after', after_hash)]:
            require(digest(directory / (Path(rel).name + '.' + suffix)) == value,
                    f'managed saved {suffix} bytes changed: {rel}')
        require(digest(REFERENCE / rel) == after_hash, f'managed output was regenerated/changed: {rel}')
    before = (directory / 'ps_ai.v.before').read_bytes()
    after = (directory / 'ps_ai.v.after').read_bytes()
    export = E3 / 'read-candidate-preparation/ps-export'
    proof = load(export / 'inverse-proof.json')
    top_proof = proof['top']
    start, end = receipt['original_top_span']
    new_start, new_end = receipt['new_top_span']
    require([start, end] == [top_proof['source_span_start'], top_proof['source_span_end_exclusive']]
            and new_start == start and 0 <= start < end <= len(before)
            and start < new_end <= len(after), 'managed top spans disagree')
    original_top = before[start:end]
    require(hashlib.sha256(original_top).hexdigest() == top_proof['original_SHA256']
            and original_top == (export / 'original-ps-ai-top.txt').read_bytes(),
            'original managed top source identity failed')
    observed_top = original_top
    for edit in reversed(top_proof['edits']):
        a, b = edit['start'], edit['end']
        require(observed_top[a:b] == edit['old'].encode('ascii'), 'top edit old-byte identity failed')
        observed_top = observed_top[:a] + edit['new'].encode('ascii') + observed_top[b:]
    require((export / 'ps_ai_read_observed.v').read_bytes()
            == top_proof['copied_timescale'].encode('ascii') + observed_top,
            'saved observed top differs from original proven edits')
    old_name, new_name = b'module ps_ai_read_observed', b'module ps_ai'
    require(observed_top.count(old_name) == 1, 'observed top module name not unique')
    managed_top = observed_top.replace(old_name, new_name, 1)
    require(after == before[:start] + managed_top + before[end:]
            and after[new_start:new_end] == managed_top,
            'managed full PS differs from only the proven output ports/assignments')
    require(after[:start] + original_top + after[new_end:] == before,
            'managed full PS exact inverse failed')
    require(before.count(b'`timescale') == after.count(b'`timescale') == 1,
            'managed original timescale changed')
    require(len(re.findall(rb'^module\s+', before, re.MULTILINE)) == 13
            and len(re.findall(rb'^module\s+', after, re.MULTILINE)) == 13,
            'managed original module count changed')
    wrapper_before = (directory / 'ps_ai_wrapper.sv.before').read_bytes()
    wrapper_after = (directory / 'ps_ai_wrapper.sv.after').read_bytes()
    old_instance = b'ps_ai_read_observed ps_ai_i('
    require(wrapper_before == (export / 'ps_ai_wrapper.sv').read_bytes()
            and wrapper_before.count(old_instance) == 1
            and wrapper_after == wrapper_before.replace(old_instance, b'ps_ai ps_ai_i(', 1),
            'wrapper managed fix is not exactly its original module-type restoration')
    for name in ['diagnostic_hp2_read', 'diagnostic_hp2_clk', 'diagnostic_hp2_resetn']:
        require(wrapper_after.count(('.' + name + '(' + name + ')').encode('ascii')) == 1,
                f'explicit managed wrapper tap absent/duplicate: {name}')
    return {'receipt': str(MANAGED_RECEIPT), 'receipt_SHA256': digest(MANAGED_RECEIPT),
            'after_SHA256': {rel: value[1] for rel, value in bound.items()},
            'only_top_output_ports_and_assignments_added': True,
            'original_module_name': 'ps_ai', 'other_original_modules_byte_identical': 12,
            'unique_original_timescale_unchanged': True,
            'full_original_exact_inverse_pass': True, 'BD_XCI_or_OOC_content_changed': False}


def compile_dependency_identity():
    directory = E3 / SETUP_STAGE
    order_path = directory / 'source-order.txt'
    order = order_path.read_text().replace('\\', '/').lower().splitlines()
    required = [PS_REL, 'rtl/hdmi_candidate/ai_read_monitor.sv', WRAPPER_REL]
    ps_ips = ['proc_sys_reset_0_1', 'util_vector_logic_0_0', 'processing_system7_0_0',
              'xbar_0', 'xbar_1', 'proc_sys_reset_0_0', 'xbar_4', 's00_regslice_0',
              's00_regslice_1', 's01_regslice_0', 'm00_regslice_0']
    for name in ps_ips:
        required.append(f'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ip/ps_ai_{name}/ps_ai_{name}.dcp')
    for rel in required:
        require(sum(line.endswith('/' + rel.lower()) for line in order) == 1,
                f'actual expanded compile order lacks unique managed PS definition: {rel}')
    unused = ['rtl/hdmi_candidate/ps_ai_read_observed.v', 'rtl/hdmi_candidate/ps_ai_original_submodules.v']
    for rel in unused:
        require(not any(line.endswith('/' + rel.lower()) for line in order),
                f'old global PS source still compiled: {rel}')
    ooc = (directory / 'OOC-state.txt').read_text().splitlines()
    for name in ps_ips:
        require(ooc.count(f'ps_ai_{name}_synth_1|synth_design Complete!|0') == 1,
                f'managed PS OOC incomplete/needs refresh: {name}')
    original_reference = ROOT / '.local/hdmi-live-20261017-r1/reference'
    ooc_hashes = {}
    for rel in required:
        if not rel.endswith('.dcp'):
            continue
        expected = digest(original_reference / rel)
        require(digest(REFERENCE / rel) == expected, f'original managed PS OOC bytes changed: {rel}')
        ooc_hashes[rel] = expected
    script_path = REFERENCE / f'fpai_demo_vivado.runs/{SYNTH_RUN}/ai7030_edif_top.tcl'
    script = script_path.read_text().replace('\\', '/')
    bd_path = (REFERENCE / BD_REL).as_posix()
    bd_lines = [line for line in script.splitlines()
                if line.strip().lower() == ('add_files ' + bd_path).lower()]
    require(len(bd_lines) == 1, 'actual new synth run does not add the original managed PS BD once')
    for rel in unused:
        require(rel not in script, f'old global PS source remains in native synth script: {rel}')
    return {'setup_compile_order_SHA256': digest(order_path), 'managed_PS_DCP_count': len(ps_ips),
            'original_full_PS_in_compile_order': True, 'unused_global_PS_sources_compiled': False,
            'managed_BD_source': BD_REL, 'actual_synth_run': SYNTH_RUN,
            'original_PS_OOC_SHA256': ooc_hashes,
            'actual_synth_script_SHA256': digest(script_path), 'actual_BD_add_files_line': bd_lines[0],
            'note': 'Vivado compile order expands managed BD into full PS HDL and OOC DCPs; native run Tcl retains add_files BD'}


def stable_sources():
    preparation = load(E3 / 'read-candidate-preparation/review.json')
    require(preparation['passed'], 'candidate preparation did not pass')
    expected = dict(preparation['protected_after'])
    for item in preparation['planned_changes']:
        expected[item['path']] = item['after_SHA256']
    expected.pop('fpai_demo_vivado.xpr', None)
    managed = managed_ps_identity()
    # Only these two reviewed source identities override the original protected
    # preparation. The failed global copies remain frozen on disk but inactive.
    expected.update(managed['after_SHA256'])
    submodule_rel = 'rtl/hdmi_candidate/ps_ai_original_submodules.v'
    top_proof = load(E3 / 'read-candidate-preparation/ps-export/inverse-proof.json')['top']
    original_ps = (MANAGED_RECEIPT.parent / 'ps_ai.v.before').read_bytes()
    start, end = top_proof['source_span_start'], top_proof['source_span_end_exclusive']
    require(0 <= start < end <= len(original_ps), 'original top source span invalid')
    expected_submodules = original_ps[:start] + original_ps[end:]
    require((REFERENCE / submodule_rel).read_bytes() == expected_submodules,
            'PS helper source differs from exact top-removal slice')
    expected[submodule_rel] = hashlib.sha256(expected_submodules).hexdigest()
    clock_rel = 'constrs_1/ai_read_clock_review.tcl'
    clock_formal = ROOT / 'FPGA/hdmi_candidate/diagnostics/ai_read_clock_review.tcl'
    require(digest(REFERENCE / clock_rel) == digest(clock_formal), 'unreviewed clock-review source change')
    expected[clock_rel] = digest(clock_formal)
    dependencies = compile_dependency_identity()
    expected.update(dependencies['original_PS_OOC_SHA256'])
    for rel, value in expected.items():
        require(digest(REFERENCE / rel) == value, f'stable source identity changed: {rel}')
    require((REFERENCE / 'constrs_1/hdmi_cdc.tcl').read_bytes() == (REFERENCE / 'constrs_1/hdmi_cdc.xdc').read_bytes(),
            'HDMI procedural constraint copies differ')
    return expected


def main():
    directory = E3 / CONSTRAINT_STAGE
    require(not (directory / 'review.json').exists(), 'refusing to overwrite constraint review')
    completed(SETUP_STAGE)
    completed(BUILD_PREFIX + 'synthesis')
    completed(CONSTRAINT_STAGE)
    binding = (directory / 'binding.txt').read_text()
    indices = parse_indices(binding)
    first = binding.splitlines()[0]
    fields = dict(re.findall(r'(\w+)=([^\s]+)', first))
    require(int(fields['source_bits']) == int(fields['capture_bits']) == len(indices), 'binding count/index mismatch')
    for name, expected in [('stable_bus_requirement',10.),('source_period',5.),('capture_period',10.)]:
        require(abs(float(fields[name])-expected) <= .001, f'binding requirement/period wrong: {name}')
    read = monitor_cdc(directory / 'read-CDC.rpt', READ_SCOPE, indices, True)
    # Discover old indices from the actual rows, then enforce the accepted708-bit
    # contract and complete pairwise correspondence rather than a count alone.
    old_rows = cdc_rows(directory / 'observer-CDC.rpt')
    old_indices = [int(re.search(re.escape(OLD_SCOPE)+r'csr_snapshot_reg\[(\d+)\]/D', row)[1])
                   for row in old_rows if re.search(r'\bCDC-15\b', row)]
    require(len(old_indices) == len(set(old_indices)) == 708, 'retained v2 bank width changed')
    old = monitor_cdc(directory / 'observer-CDC.rpt', OLD_SCOPE, sorted(old_indices), False)
    stdout = (directory / 'stdout.txt').read_text()
    retained = re.findall(r'AI_MONITOR_STABLE_BUS_ACTIVE source_bits=(\d+) capture_bits=(\d+) max_ns=([\d.]+) source_period=([\d.]+) capture_period=([\d.]+)', stdout)
    require(len(retained) == 1 and tuple(float(x) for x in retained[0]) == (708.,708.,10.,5.,10.),
            'retained v2 actual max-delay binding missing/wrong')
    timing = (directory / 'read-snapshot-path.rpt').read_text()
    require(re.search(r'Requirement:\s+10\.000ns', timing) and 'VIOLATED' not in timing
            and 'Slack (MET)' in timing, 'read snapshot path timing absent/failed')
    endpoints = snapshot_endpoints(directory / 'read-snapshot-endpoints.txt', indices)
    clocks = clock_taps(directory / 'clock-taps.txt', indices)
    sources = stable_sources()
    review = {'route_prerequisite_pass': True, 'scope': 'isolated diagnostic route only; no board acceptance',
              'read_bits': len(indices), 'read_indices': indices, 'read_CDC': read,
              'retained_v2_bits': 708, 'retained_v2_indices': sorted(old_indices), 'retained_v2_CDC': old,
              'read_snapshot_requirement_ns': 10., 'read_snapshot_endpoints': endpoints,
              'actual_clock_taps': clocks, 'setup_XPR_identity': setup_xpr_identity(),
              'managed_PS_source_identity': managed_ps_identity(),
              'actual_managed_PS_compile_dependencies': compile_dependency_identity(),
              'source_sha256': sources, 'new_timing_or_DRC_waiver': False,
              'review_driver_SHA256': digest(Path(__file__)),
              'new_BOOT_or_reboot_authorized': False,
              'manual_CDC_scope': 'held source_snapshot until later explicit ARM; independent two-stage ARM/FREEZE request/ack; coordinated hard reset and local three-stage releases; only four first D and six release CLR pins cut',
              'raw_async_metadata_crossing_accepted': False}
    (directory / 'review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
    print(json.dumps({key: review[key] for key in ['route_prerequisite_pass','read_bits','retained_v2_bits','actual_clock_taps']},indent=2))


if __name__ == '__main__':
    main()
