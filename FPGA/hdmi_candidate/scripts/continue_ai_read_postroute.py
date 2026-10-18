"""One bounded r6 physical timing experiment from the frozen r4 checkpoint.

No project-run status is fabricated or reused. Bootstrap opens/checks/closes the
checkpoint; route resumes only routing and its original complete factory hook.
Routing is followed by one explicit four-option post-route optimization,
before the first complete original JFM route-post hook. No route retry,
retiming or clock optimization is added. Bit generation remains disabled.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import re
import sys
import time

sys.dont_write_bytecode = True
R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-live-20261017-r3'
E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
REF = W / 'reference'
NATIVE = REF / 'fpai_demo_vivado.runs/route_read_v3r6'
CHECKPOINT = E / 'checkpoints-before-route-r4/ai7030_edif_top_physopt.dcp'
CHECKPOINT_SHA = 'f58a5f8e6f432be7e656de5ee32eae5ae63b491d5a5cb1055425ee32895525d9'
OLD_NATIVE = E / 'checkpoints-before-route-r4/ai7030_edif_top.tcl'
OLD_NATIVE_SHA = 'fe2a27e53a4131a1503d5e28dea02a79dceaef954d56bf3912a56b642a91269a'
GATE = E / 'read-v3r3-constraints-r3/review.json'
INSTALLED = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/toolchain-identity-review.json'
TOOL = Path('D:/vivado18.3/Vivado/2018.3')
ROUTED = NATIVE / 'ai7030_edif_top_routed.dcp'
ROUTED_SHA_FILE = E / 'read-v3r6-route/routed-checkpoint.json'
SOURCE_DRIVER = Path(__file__).with_name('continue_ai_read_checkpoint.py')
SOURCE_DRIVER_SHA = 'ee11b66896bb84886b186a4667fd4d5c871ec7c404bcc034e56637bacd01504b'
POSTROUTE_PARAMETERS = ['-placement_opt', '-routing_opt', '-rewire', '-critical_pin_opt']
POSTROUTE_ORDER = ['original_route_design_NoTimingRelaxation', 'four_option_postroute_phys_opt',
                   'first_complete_original_JFM_route_post', 'original_checkpoint_and_native_reports']
BIT_NATIVE = R / '.local/hdmi-live-20261017-r1/reference/fpai_demo_vivado.runs/impl_ai_monitor_v2/ai7030_edif_top.tcl'
BIT_NATIVE_SHA = '7d5753819b051896b0753cac7ee66615a9c8326f2c4d0699fed01967fdcd95ed'
BIT_OLD_RESULT = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r2/monitor-v2-bit/execution.json'
BIT_OLD_LOG = BIT_OLD_RESULT.with_name('stdout.txt')
BIT_REVIEW = E / 'read-v3r6-reports/review.json'
BIT = NATIVE / 'ai7030_edif_top.bit'
BIT_HOOKS = ['ip_patch/project_execution_guard.tcl', 'ip_patch/run.tcl', 'ip_patch/all_src_files.tcl',
             'ip_patch/process_control/write_bitstream_pre.tcl', 'ip_patch/process_control/write_bitstream_post.tcl']
DERIVED_NAMES = ['call_procise_disable_icap.bat', 'procise_run_disable_icap.tcl']
HOOKS = ['ip_patch/project_execution_guard.tcl', 'ip_patch/run.tcl', 'ip_patch/all_src_files.tcl',
         'ip_patch/process_control/implementation_route_post.tcl',
         'ip_patch/process_control/implementation_opt_post.tcl',
         'ip_patch/process_control/implementation_opt_pre.tcl',
         'ip_patch/process_control/write_bitstream_pre.tcl',
         'ip_patch/process_control/implementation_opt_pre_hdmi.tcl',
         'constrs_1/hdmi_cdc.tcl', 'constrs_1/ai_monitor_cdc.tcl',
         'constrs_1/ai_read_monitor_cdc.tcl', 'constrs_1/ai_read_clock_review.tcl']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_new(path, value):
    with path.open('x', encoding='utf-8') as file:
        file.write(json.dumps(value, indent=2) + '\n')


def literal_values(path, name):
    """Read source literals with AST; never execute a previous build driver."""
    tree = ast.parse(path.read_bytes(), filename=str(path))
    values = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name
                                               for target in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                values.append((node.lineno, node.value.value))
    return [value for _, value in sorted(values)]


def postroute_transform(route):
    """Add one optimizer before the original hook; prove the entire inverse."""
    insertion = r'''
# R6_POSTROUTE_PHYSICAL_EXPERIMENT_BEGIN
proc ai_read_postroute_record {event} {
 set channel [open {@@OUT@@/postroute-order.txt} a]
 puts $channel $event
 close $channel
}
proc ai_read_postroute_status {label} {
 set report [report_route_status -return_string -ignore_cache]
 set channel [open "@@OUT@@/postroute-$label-route-status.rpt" {WRONLY CREAT EXCL}]
 puts $channel $report
 close $channel
 set fully [report_route_status -boolean_check ROUTED_FULLY -ignore_cache]
 set errors [report_route_status -boolean_check ERRORS_IN_ROUTES -ignore_cache]
 set channel [open "@@OUT@@/postroute-$label-checks.txt" {WRONLY CREAT EXCL}]
 puts $channel "ROUTED_FULLY|$fully"
 puts $channel "ERRORS_IN_ROUTES|$errors"
 close $channel
 ai_read_postroute_record "ROUTE_STATUS|$label|$fully|$errors"
 if {$fully!=1 || $errors!=0} {error "R6_POSTROUTE_ROUTING_BOUNDARY_FAILED $label fully=$fully errors=$errors"}
}
set ai_read_postroute_order_channel [open {@@OUT@@/postroute-order.txt} {WRONLY CREAT EXCL}]
close $ai_read_postroute_order_channel
ai_read_postroute_record ORIGINAL_ROUTE_COMPLETED
ai_read_postroute_status before-opt
ai_read_postroute_record {PHYS_OPT_BEGIN|-placement_opt -routing_opt -rewire -critical_pin_opt}
phys_opt_design -placement_opt -routing_opt -rewire -critical_pin_opt
ai_read_postroute_record PHYS_OPT_END
ai_read_postroute_status after-opt
ai_read_postroute_record JFM_ROUTE_POST_FIRST_CALL_BEGIN
# R6_POSTROUTE_PHYSICAL_EXPERIMENT_END
'''
    after_hook = ('  ai_read_postroute_record JFM_ROUTE_POST_FIRST_CALL_END\n'
                  '  ai_read_postroute_status after-jfm-hook\n')
    anchor = '  route_design -directive NoTimingRelaxation\n'
    finish = '  write_checkpoint -force ai7030_edif_top_routed.dcp\n'
    require(route.count(anchor) == route.count(finish) == 1, 'r6 native route/hook boundary ambiguous')
    require(insertion not in route and after_hook not in route, 'r6 optimization already present')
    changed = route.replace(anchor, anchor + insertion).replace(finish, after_hook + finish)
    inverse = changed.replace(insertion, '').replace(after_hook, '')
    require(inverse == route, 'r6 inverse differs from the complete original named route block')
    native = OLD_NATIVE.read_text()
    marker = '\nstart_step route_design\n'
    require(native.count(marker) == 1, 'frozen native route boundary changed')
    restored = native.split(marker, 1)[0] + '\n' + inverse.replace('route_read_v3r6', 'impl_read_v3r4')
    require(restored == native, 'r6 inverse does not recover the complete frozen native text')
    raw = OLD_NATIVE.read_bytes()
    ending = '\r\n' if raw.count(b'\n') == raw.count(b'\r\n') else '\n'
    require(restored.replace('\n', ending).encode('utf-8') == raw, 'r6 inverse does not recover frozen native bytes')
    return changed, {'original_named_route_SHA256': hashlib.sha256(route.encode()).hexdigest(),
                     'optimized_route_SHA256': hashlib.sha256(changed.encode()).hexdigest(),
                     'inverse_exact_original_named_route': True, 'inverse_exact_complete_frozen_native_bytes': True}


def postroute_configuration():
    native = OLD_NATIVE.read_text()
    original = 'start_step route_design\n' + native.split('\nstart_step route_design\n', 1)[1]
    _, transform = postroute_transform(original.replace('impl_read_v3r4', 'route_read_v3r6'))
    return {'parameters': POSTROUTE_PARAMETERS, 'source_driver_path': str(SOURCE_DRIVER),
            'source_driver_SHA256': SOURCE_DRIVER_SHA, 'order': POSTROUTE_ORDER,
            'no_additional_route_pass': True, 'no_retime': True, 'no_clock_opt': True,
            'JFM_route_post_first_complete_call_after_optimization': True,
            'protected_source_count': 937, 'installed_file_count': 41,
            'physical_implementation_change': True, 'RTL_and_external_interface_change': False,
            'timing_constraints_frequencies_DRC_profile_unchanged': True,
            'new_DRC_or_timing_waiver': False, 'inverse_transform': transform,
            'scope': 'one bounded isolated physical experiment; FMQL compatibility and timing remain actual gates'}


def pieces():
    require(sha(OLD_NATIVE) == OLD_NATIVE_SHA, 'frozen original native Tcl identity changed')
    native = OLD_NATIVE.read_text()
    marker = '\nstart_step init_design\n'
    require(native.count(marker) == 1, 'original native header boundary ambiguous')
    header = native.split(marker, 1)[0]
    marker = '\nstart_step route_design\n'
    require(native.count(marker) == 1, 'original route block ambiguous')
    route = 'start_step route_design\n' + native.split(marker, 1)[1]
    require(not re.search(r'^\s*(?:opt_design|place_design|phys_opt_design|write_bitstream)\b', route, re.MULTILINE),
            'route-only block contains another implementation phase')
    require(route.count('route_design -directive NoTimingRelaxation') == 1
            and route.count('write_checkpoint -force ai7030_edif_top_routed.dcp') == 1,
            'original route command/checkpoint contract changed')
    route = route.replace('impl_read_v3r4', 'route_read_v3r6')
    route, _ = postroute_transform(route)
    current = Path(__file__).with_name('continue_ai_read_candidate.py')
    endpoints = literal_values(current, 'endpoint_proc')
    extra = literal_values(current, 'extra')
    require(len(endpoints) == len(extra) == 1, 'read-driver endpoint/report literal ambiguous')
    legacy = Path(__file__).with_name('continue_ai_monitor_candidate.py')
    require(sha(legacy) == 'e30ffbe3fb4231096ab19f6423daaf39994c2427ed52a73086ca07da8cc06941',
            'reviewed legacy report body source changed')
    bodies = literal_values(legacy, 'body')
    require(len(bodies) == 5, 'legacy Tcl body count changed')
    reports = bodies[3]
    opening = ('open_project {@@REF@@/fpai_demo_vivado.xpr}\n'
               'set_param general.maxThreads 2\nopen_run impl_ai_monitor_v2')
    require(reports.count(opening) == 1 and reports.count('close_project') == 1,
            'legacy report opening/closing contract changed')
    reports = reports.replace(opening, '')
    reports = reports.replace('close_project', extra[0] + '\nclose_design')
    reports = reports.replace('ai-monitor-routed.dcp', 'ai-read-routed.dcp')
    require('open_project' not in reports and 'open_run' not in reports and 'launch_runs' not in reports,
            'report stage still depends on managed run state')
    return header, route, endpoints[0], reports


def preflight():
    require(sha(SOURCE_DRIVER) == SOURCE_DRIVER_SHA, 'original r5 source driver changed')
    gate = load(GATE)
    require(gate['route_prerequisite_pass'] and gate['read_bits'] == 2768,
            'accepted constraint-r3 gate absent/changed')
    sources = gate['source_sha256']
    require(len(sources) == 937, 'protected source count changed')
    for relative, expected in sources.items():
        require(sha(REF / relative) == expected, 'protected source identity changed: ' + relative)
    installed = load(INSTALLED)
    require(installed['matching'] and installed['checked_files'] == len(installed['actual']) == 41,
            'installed identity ledger changed')
    for relative, expected in installed['actual'].items():
        require(sha(TOOL / relative) == expected, 'installed library changed: ' + relative)
    require(sha(CHECKPOINT) == CHECKPOINT_SHA, 'frozen physical checkpoint changed')
    for relative in HOOKS:
        require(relative in sources and sha(REF / relative) == sources[relative],
                'unbound hook/clock/constraint source: ' + relative)
    factory = {}
    for relative in ['ip_patch/process_control/implementation_opt_pre.tcl',
                     'ip_patch/process_control/write_bitstream_pre.tcl']:
        lines = (REF / relative).read_text().splitlines()
        records = [{'line': n, 'raw': line} for n, line in enumerate(lines, 1)
                   if re.search(r'set_property\s+IS_ENABLED\s+0\s+\[get_drc_checks\s+REQP-(44|46|52|56)\]', line)]
        require(set(re.findall(r'REQP-\d+', '\n'.join(row['raw'] for row in records)))
                == {'REQP-44', 'REQP-46', 'REQP-52', 'REQP-56'}, 'original factory DRC whitelist changed')
        factory[relative] = {'SHA256': sha(REF / relative), 'original_disable_lines': records}
    old_drc = R / '.local/hdmi-live-20261017-r1/reference/fpai_demo_vivado.runs/impl_ai_monitor_v2/ai7030_edif_top_drc_routed.rpt'
    disabled = [{'line': n, 'raw': line} for n, line in enumerate(old_drc.read_text().splitlines(), 1)
                if line.startswith('The following rules are disabled:')]
    require([row['raw'] for row in disabled] == ['The following rules are disabled: REQP-44, REQP-46, REQP-52, REQP-56'],
            'old actual routed factory DRC profile changed')
    factory['old_actual_routed_DRC'] = {'path': str(old_drc), 'SHA256': sha(old_drc), 'lines': disabled}
    header, route, endpoints, reports = pieces()
    return {'gate_SHA256': sha(GATE), 'source_sha256': sources,
            'installed_identity_ledger_SHA256': sha(INSTALLED), 'installed_sha256': installed['actual'],
            'checkpoint_SHA256': CHECKPOINT_SHA, 'original_native_SHA256': OLD_NATIVE_SHA,
            'hook_sha256': {relative: sources[relative] for relative in HOOKS},
            'existing_factory_DRC_profile_proof': factory,
            'route_block_SHA256': hashlib.sha256(route.encode()).hexdigest(),
            'native_directory': str(NATIVE), 'parent_synthesis_provenance': 'synth_read_v3r3',
            'hardware_change': False, 'new_timing_or_DRC_waiver': False,
            'postroute_optimization': postroute_configuration()}


def substitutions(text):
    return text.replace('@@NATIVE@@', NATIVE.as_posix()).replace('@@PHYSOPT@@', CHECKPOINT.as_posix()).replace(
        '@@EVIDENCE@@', E.as_posix())


def common_tcl(checkpoint, audit=True):
    context = r'''
cd {@@NATIVE@@}
if {[file normalize [file join [pwd] ../..]] ne [file normalize {@@REF@@}]} {error "CHECKPOINT_JFM_CWD_WRONG"}
open_checkpoint {CHECKPOINT_FILE}
source {@@REF@@/ip_patch/project_execution_guard.tcl}
set context_directory [get_property DIRECTORY [current_project]]
set context_part [get_property PART [current_project]]
if {$context_directory ne "."} {error "CHECKPOINT_NON_DOT_DIRECTORY $context_directory"}
if {$context_part ne "xc7z030ffg676-2"} {error "CHECKPOINT_PART_CHANGED $context_part"}
set ::env(JFM_PATH) [file normalize {@@REF@@}]
if {[file normalize $::env(JFM_PATH)] ne [file normalize [file join [pwd] ../..]]} {error "CHECKPOINT_JFM_PATH_WRONG"}
set f [open {@@OUT@@/checkpoint-context.txt} {WRONLY CREAT EXCL}]
puts $f "DIRECTORY|$context_directory"
puts $f "PART|$context_part"
puts $f "CWD|[pwd]"
puts $f "JFM_PATH|$::env(JFM_PATH)"
puts $f "MAX_THREADS|[get_param general.maxThreads]"
foreach rule {REQP-44 REQP-46 REQP-52 REQP-56} {puts $f "DRC_BEFORE|$rule|[get_property IS_ENABLED [get_drc_checks $rule]]"}
close $f
check_managed_ps
set src [get_cells -quiet -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/source_snapshot_reg\[[0-9]+\]$}]
set dst [get_cells -quiet -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/csr_snapshot_reg\[[0-9]+\]$}]
if {[llength $src]!=2768 || [llength $dst]!=2768} {error "CHECKPOINT_READ_BANK_CHANGED"}
set f [open {@@OUT@@/checkpoint-binding.txt} {WRONLY CREAT EXCL}]
foreach {label cells} [list source $src capture $dst] {
 set indices {}
 foreach c $cells {if {![regexp {\[([0-9]+)\]$} $c unused index]} {error "CHECKPOINT_INDEX_MISSING"};lappend indices $index}
 set indices [lsort -integer -unique $indices]
 puts $f "$label=$indices"
}
close $f
'''.replace('CHECKPOINT_FILE', checkpoint.as_posix())
    if not audit:
        return context
    return context + r'''
ai_read_dump_endpoints {@@OUT@@/checkpoint-endpoints.txt} $src $dst
set ::ai_read_clock_report {@@OUT@@/clock-taps.txt}
source {@@REF@@/constrs_1/ai_read_clock_review.tcl}
'''


def bit_pieces():
    """Bind the previously successful native bit sequence, without executing it."""
    require(sha(BIT_NATIVE) == BIT_NATIVE_SHA, 'reviewed successful bit native Tcl changed')
    original_bytes = BIT_NATIVE.read_bytes()
    require(original_bytes.count(b'\r') == original_bytes.count(b'\r\n')
            and original_bytes.count(b'\n') == original_bytes.count(b'\r\n'),
            'reviewed native newline identity changed')
    native = BIT_NATIVE.read_text()
    marker = '\nstart_step write_bitstream\n'
    require(native.count(marker) == 1, 'successful bit native header/block boundary ambiguous')
    header, block = native.split(marker, 1)
    block = 'start_step write_bitstream\n' + block
    old_ref = (R / '.local/hdmi-live-20261017-r1/reference').as_posix()
    require(block.count(old_ref) == 7, 'successful bit native reference count changed')
    block = block.replace(old_ref, REF.as_posix())
    opening = '  open_checkpoint ai7030_edif_top_routed.dcp\n'
    require(block.count(opening) == 1, 'successful bit native checkpoint opening ambiguous')
    block = block.replace(opening, '  # Routed checkpoint was opened and audited by common_tcl.\n')
    anchor = '  set_property XPM_LIBRARIES {XPM_CDC XPM_MEMORY} [current_project]\n'
    require(block.count(anchor) == 1, 'successful bit pre-hook completion boundary ambiguous')
    block = block.replace(anchor, '  ai_read_bit_assert_context after_pre\n' + anchor)
    anchor = '  write_bitstream -force ai7030_edif_top.bit \n'
    require(block.count(anchor) == 1, 'successful native bit command ambiguous')
    block = block.replace(anchor, '  if {[file exists ai7030_edif_top.bit]} {error "BIT_TARGET_ALREADY_EXISTS"}\n' + anchor)
    anchor = '  catch { write_sysdef '
    require(block.count(anchor) == 1, 'successful bit post-hook completion boundary ambiguous')
    block = block.replace(anchor, '  ai_read_bit_assert_context after_post\n' + anchor)
    require(block.count('source ' + REF.as_posix() + '/ip_patch/process_control/write_bitstream_pre.tcl') == 2
            and block.count('source ' + REF.as_posix() + '/ip_patch/process_control/write_bitstream_post.tcl') == 2,
            'complete original factory pre/post calls were not retained')
    # Reverse every permitted edit. This comparison covers the full native body,
    # not a list of selected commands or a newly written approximation.
    reverse = block.replace('  ai_read_bit_assert_context after_pre\n', '').replace(
        '  ai_read_bit_assert_context after_post\n', '').replace(
        '  if {[file exists ai7030_edif_top.bit]} {error "BIT_TARGET_ALREADY_EXISTS"}\n', '')
    reverse = reverse.replace('  # Routed checkpoint was opened and audited by common_tcl.\n', opening)
    reverse = reverse.replace(REF.as_posix(), old_ref)
    require(header + '\n' + reverse == native, 'bit native transform is not exactly reversible')
    require((header + '\n' + reverse).replace('\n', '\r\n').encode('utf-8') == original_bytes,
            'bit native inverse does not recover original file bytes')
    return header, block, {'original_SHA256': BIT_NATIVE_SHA,
                          'transformed_block_SHA256': hashlib.sha256(block.encode()).hexdigest(),
                          'inverse_exact_original_text': True, 'inverse_exact_original_bytes': True,
                          'edits': ['reference path only', 'remove duplicate checkpoint opening',
                                    'add after-pre and after-post context assertions', 'reject existing bit target']}


def bit_preflight(proof):
    """Bit-only bindings; do not change the already executed bootstrap proof."""
    check_completed('reports')
    require(sha(BIT_OLD_RESULT) == '123c5b51c19b980e9debaa2d0d1503aa858c4f98e82a8409102b6e94bcee8468'
            and sha(BIT_OLD_LOG) == '09243e976702c2c6abc40213cce87e7e48c3267a380eb8db1e35dc538d5765b0',
            'old successful bit execution evidence changed')
    require(load(BIT_OLD_RESULT)['exit'] == 0 and not load(BIT_OLD_RESULT)['stopped_by_monitor'],
            'old successful bit result is not a success')
    old_lines = BIT_OLD_LOG.read_text().splitlines()
    evidence = [{'line': n, 'raw': line} for n, line in enumerate(old_lines, 1)
                if n >= 2047 and any(text in line for text in [
                    'open_checkpoint ai7030_edif_top_routed.dcp', 'open_project:', 'step 5',
                    'write_bitstream_pre.tcl', 'write_bitstream_post.tcl',
                    'write_bitstream completed successfully', 'Orginal bit path is',
                    'call_procise_disable_icap.bat is generated successfully'])]
    require(any(row['raw'] == 'write_bitstream completed successfully' for row in evidence),
            'old successful full bit completion missing')
    formal = load(BIT_REVIEW)
    require(formal['bit_generation_prerequisite_pass'] is True and formal['candidate_run'] == 'route_read_v3r6'
            and formal['managed_run'] is False and formal['read_bits'] == 2768,
            'formal routed bit-generation prerequisite is not passed')
    require(formal['source_sha256'] == proof['source_sha256'], 'formal routed protected source identity changed')
    require(formal['review_driver_SHA256'] == sha(Path(__file__).with_name('review_ai_read_route.py')),
            'formal routed reviewer changed after acceptance')
    routed = load(ROUTED_SHA_FILE)
    require(formal['checkpoint_continuation']['routed_checkpoint'] == routed
            and formal['checkpoint_continuation']['source_physical_SHA256'] == CHECKPOINT_SHA,
            'formal routed checkpoint lineage changed')
    require(Path(routed['path']).resolve() == ROUTED.resolve() and sha(ROUTED) == routed['SHA256']
            and ROUTED.stat().st_size == routed['bytes']
            and routed['source_physical_checkpoint_SHA256'] == CHECKPOINT_SHA,
            'actual bit input routed checkpoint identity changed')
    hooks = {}
    for relative in BIT_HOOKS:
        require(relative in proof['source_sha256'] and sha(REF / relative) == proof['source_sha256'][relative],
                'unbound bit factory hook: ' + relative)
        hooks[relative] = proof['source_sha256'][relative]
    for relative in ['ip_patch/process_control/write_bitstream_pre.tcl',
                     'ip_patch/process_control/write_bitstream_post.tcl']:
        text = (REF / relative).read_text()
        require(text.count('-change_speed FALSE') == 1 and '-change_speed TRUE' not in text,
                'factory bit speed-library setting changed')
    _, _, transform = bit_pieces()
    derived = {name: {'original_path': str(REF / name),
                      'redirected_path': str(E / 'read-v3r6-bit/factory-derived' / name),
                      'original_protected': name in proof['source_sha256'],
                      'original_exists_before': (REF / name).exists(),
                      'original_before_SHA256': sha(REF / name) if (REF / name).exists() else None}
               for name in DERIVED_NAMES}
    require(derived['procise_run_disable_icap.tcl']['original_protected']
            and not derived['call_procise_disable_icap.bat']['original_protected'],
            'reviewed factory derived-output protection boundary changed')
    return {'formal_routed_review_SHA256': sha(BIT_REVIEW), 'source_routed_checkpoint_SHA256': routed['SHA256'],
            'source_physical_checkpoint_SHA256': CHECKPOINT_SHA, 'factory_hook_SHA256': hooks,
            'successful_native_path': str(BIT_NATIVE), 'successful_native_SHA256': BIT_NATIVE_SHA,
            'successful_execution_SHA256': sha(BIT_OLD_RESULT), 'successful_stdout_SHA256': sha(BIT_OLD_LOG),
            'successful_stdout_evidence': evidence, 'native_transform': transform,
            'factory_derived_isolation_plan': {'policy': 'exact-two-absolute-open-write-targets-only',
                'original_sources_unchanged_required': True, 'raw_batch_execution_forbidden': True,
                'outputs': derived}}


def bit_tcl():
    """Strict public-command checks around the complete original bit hooks."""
    header, block, _ = bit_pieces()
    checks = r'''
# The unchanged factory post generates two project-level helper files. Keep
# both original paths untouched and archive their exact output in this phase.
# Unknown mutation APIs or open modes for these two targets fail before write.
if {[file exists {@@OUT@@/factory-derived}]} {error "BIT_DERIVED_DIRECTORY_ALREADY_EXISTS"}
file mkdir {@@OUT@@/factory-derived}
set ::ai_read_bit_derived_targets [dict create]
set ::ai_read_bit_derived_counts [dict create]
foreach name {call_procise_disable_icap.bat procise_run_disable_icap.tcl} {
 set original [file normalize [file join {@@REF@@} $name]]
 dict set ::ai_read_bit_derived_targets [string tolower $original] [file normalize [file join {@@OUT@@/factory-derived} $name]]
 dict set ::ai_read_bit_derived_counts [string tolower $original] 0
}
set f [open {@@OUT@@/factory-derived-writes.txt} {WRONLY CREAT EXCL}];close $f
set f [open {@@OUT@@/factory-exec-attempts.txt} {WRONLY CREAT EXCL}];close $f
set ::ai_read_bit_hook_phase before_pre
if {[llength [info commands ai_read_bit_original_open]] || [llength [info commands ai_read_bit_original_file]]
    || [llength [info commands ai_read_bit_original_exec]]} {error "BIT_DERIVED_WRAPPER_ALREADY_EXISTS"}
rename open ai_read_bit_original_open
rename file ai_read_bit_original_file
rename exec ai_read_bit_original_exec
proc open {p args} {
 set normalized [ai_read_bit_original_file normalize $p]
 set key [string tolower $normalized]
 if {[dict exists $::ai_read_bit_derived_targets $key]} {
  set mode [expr {[llength $args] ? [lindex $args 0] : "r"}]
  if {$mode ni {r rb}} {
   if {[llength $args]!=1 || $mode ni {w wb} || [ai_read_bit_original_file pathtype $p] ne "absolute"} {
    error "BIT_DERIVED_UNREVIEWED_OPEN_MODE $p $args"
   }
   if {$::ai_read_bit_hook_phase ne "after_pre"} {error "BIT_DERIVED_WRITE_OUTSIDE_POST $p"}
   set target [dict get $::ai_read_bit_derived_targets $key]
   if {[dict get $::ai_read_bit_derived_counts $key]!=0 || [ai_read_bit_original_file exists $target]} {
    error "BIT_DERIVED_OUTPUT_ALREADY_WRITTEN $p"
   }
   set f [ai_read_bit_original_open {@@OUT@@/factory-derived-writes.txt} a]
   puts $f "$normalized|$target|$mode"
   close $f
   set channel [uplevel 1 [linsert $args 0 ai_read_bit_original_open $target]]
   dict incr ::ai_read_bit_derived_counts $key
   return $channel
  }
 }
 return [uplevel 1 [linsert $args 0 ai_read_bit_original_open $p]]
}
proc file {sub args} {
 set writes {}
 if {$sub eq "copy"} {set writes [list [lindex $args end]]
 } elseif {$sub eq "rename"} {set writes [lrange $args end-1 end]
 } elseif {$sub in {delete mkdir attributes mtime atime link}} {set writes $args}
 foreach p $writes {
  if {[string index $p 0] ne "-" && [dict exists $::ai_read_bit_derived_targets [string tolower [ai_read_bit_original_file normalize $p]]]} {
   error "BIT_DERIVED_UNREVIEWED_FILE_MUTATION $sub $args"
  }
 }
 return [uplevel 1 [linsert $args 0 ai_read_bit_original_file $sub]]
}
proc exec args {
 set text [string tolower [join $args " "]]
 set f [ai_read_bit_original_open {@@OUT@@/factory-exec-attempts.txt} a]
 puts $f [list $args]
 close $f
 foreach stem {call_procise_disable_icap procise_run_disable_icap} {
  if {[string first $stem $text]>=0} {error "BIT_RAW_DERIVED_BATCH_EXECUTION_FORBIDDEN $args"}
 }
 return [uplevel 1 [linsert $args 0 ai_read_bit_original_exec]]
}
# Original pre opens the same reference XPR and closes it. Require the returned
# in-memory design, primitive identity and placed geometry to remain identical.
proc ai_read_bit_capture_context {label} {
 set project [current_project]
 set design [current_design]
 set directory [get_property DIRECTORY $project]
 set part [get_property PART $project]
 if {$directory ne "." || $part ne "xc7z030ffg676-2"} {error "BIT_CONTEXT_NOT_PHYSICAL_CHECKPOINT $label"}
 set leaves [lsort -dictionary [get_cells -quiet -hier -filter {IS_PRIMITIVE == 1}]]
 set count [llength $leaves]
 if {$count==0} {error "BIT_LEAF_SET_EMPTY $label"}
 set names [get_property NAME $leaves]
 set refs [get_property REF_NAME $leaves]
 set locs [get_property LOC $leaves]
 set bels [get_property BEL $leaves]
 foreach values [list $names $refs $locs $bels] {
  if {[llength $values]!=$count} {error "BIT_LEAF_GEOMETRY_PROPERTY_COUNT $label"}
 }
 set f [open "@@OUT@@/bit-leaf-geometry-$label.txt" {WRONLY CREAT EXCL}]
 foreach name $names ref $refs loc $locs bel $bels {puts $f [list $name $ref $loc $bel]}
 close $f
 set digest [md5::md5 -hex [list $names $refs $locs $bels]]
 return [list $project $design $directory $part $count $digest]
}
proc ai_read_bit_assert_context {label} {
 set actual [ai_read_bit_capture_context $label]
 if {$actual ne $::ai_read_bit_initial_context} {error "BIT_INMEMORY_CONTEXT_OR_LEAF_GEOMETRY_CHANGED $label"}
 if {$::ai_read_bit_opened_xpr!=1} {error "BIT_EXACT_REFERENCE_PROJECT_NOT_OPENED_ONCE $label"}
 set f [open "@@OUT@@/bit-context-$label.txt" {WRONLY CREAT EXCL}]
 foreach key {same_inmemory_project_design same_leaf_geometry_after_pre exact_reference_XPR_opened DIRECTORY_dot part_unchanged} {
  puts $f "$key|true"
 }
 puts $f "physical_context|$actual"
 close $f
 set ::ai_read_bit_hook_phase $label
 if {$label eq "after_post"} {
  dict for {original target} $::ai_read_bit_derived_targets {
   if {[dict get $::ai_read_bit_derived_counts $original]!=1 || ![file exists $target] || [file size $target]<=0} {
    error "BIT_DERIVED_OUTPUT_MISSING_OR_REPEATED $original"
   }
  }
 }
}
if {[llength [info commands ai_read_original_open_project]]} {error "BIT_OPEN_PROJECT_WRAPPER_ALREADY_EXISTS"}
set ::ai_read_bit_allowed_xpr [file normalize {@@REF@@/fpai_demo_vivado.xpr}]
set ::ai_read_bit_opened_xpr 0
rename open_project ai_read_original_open_project
proc open_project args {
 if {[llength $args]!=1 || [file normalize [lindex $args 0]] ne $::ai_read_bit_allowed_xpr} {
  error "BIT_FACTORY_OPENED_UNEXPECTED_PROJECT $args"
 }
 if {$::ai_read_bit_opened_xpr!=0} {error "BIT_REFERENCE_PROJECT_OPENED_MORE_THAN_ONCE"}
 set f [open {@@OUT@@/hook-open-project.txt} {WRONLY CREAT EXCL}]
 puts $f "path|[file normalize [lindex $args 0]]"
 close $f
 set result [uplevel 1 [linsert $args 0 ai_read_original_open_project]]
 incr ::ai_read_bit_opened_xpr
 return $result
}
if {[file exists ai7030_edif_top.bit] || [file exists .write_bitstream.begin.rst]
    || [file exists .write_bitstream.end.rst] || [file exists .write_bitstream.error.rst]} {error "BIT_NATIVE_TARGET_ALREADY_USED"}
set ::ai_read_bit_initial_context [ai_read_bit_capture_context before_pre]
'''
    end = r'''
if {![file exists ai7030_edif_top.bit] || [file size ai7030_edif_top.bit]<=0
    || ![file exists .write_bitstream.end.rst] || [file exists .write_bitstream.error.rst]} {error "BIT_NATIVE_WRITE_NOT_COMPLETED"}
if {[llength [glob -nocomplain .*.fail]]} {error "BIT_NATIVE_REPORT_FAILED"}
rename open_project {}
rename ai_read_original_open_project open_project
rename open {}
rename ai_read_bit_original_open open
rename file {}
rename ai_read_bit_original_file file
rename exec {}
rename ai_read_bit_original_exec exec
check_managed_ps
close_design
puts "AI_READ_CHECKPOINT_RAW_BIT_COMPLETE_NO_BOARD_OPERATION"
'''
    return common_tcl(ROUTED) + checks + header + '\n' + block + end


def build_tcl(mode):
    require(mode != 'bit', 'r6 bit remains disabled pending an actual complete r6 routed review and separate integration')
    header, route, endpoints, reports = pieces()
    checkpoint = ROUTED if mode in {'reports', 'bit'} else CHECKPOINT
    body = bit_tcl() if mode == 'bit' else common_tcl(checkpoint, audit=mode != 'reports')
    if mode == 'bit':
        pass
    elif mode == 'bootstrap':
        body += '\nclose_design\nputs "AI_READ_CHECKPOINT_BOOTSTRAP_ONLY_NO_ROUTE"\n'
    elif mode == 'route':
        body += r'''
# Restore only the original factory rule profile in this new tool session.
# Guard enforces this exact existing whitelist; no new rule is disabled.
set f [open {@@OUT@@/factory-DRC-restored.txt} {WRONLY CREAT EXCL}]
foreach rule {REQP-44 REQP-46 REQP-52 REQP-56} {
 set_property IS_ENABLED 0 [get_drc_checks $rule]
 puts $f "$rule|[get_property IS_ENABLED [get_drc_checks $rule]]"
}
close $f
'''
        body += header + '\n' + route + r'''
if {![file exists ai7030_edif_top_routed.dcp] || ![file exists .route_design.end.rst]} {error "CHECKPOINT_ROUTE_NOT_COMPLETE"}
if {[llength [glob -nocomplain .*.fail]]} {error "CHECKPOINT_NATIVE_REPORT_FAILED"}
check_managed_ps
close_design
puts "AI_READ_CHECKPOINT_ROUTED_NOT_REVIEWED_NO_BIT"
'''
    else:
        body += reports
    tcl = 'if {[catch {\n' + endpoints + '\n' + body + r'''
} result]} {puts "AI_READ_CHECKPOINT_STAGE_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
    return substitutions(tcl)


def native_inventory():
    return {path.relative_to(NATIVE).as_posix(): sha(path) for path in sorted(NATIVE.rglob('*')) if path.is_file()}


def settled_native_inventory():
    """After owned EDA exits, wait at most 10s; never filter native files."""
    started = time.monotonic()
    observations, previous, last = [], None, None
    while True:
        elapsed = time.monotonic() - started
        try:
            actual = native_inventory()
        except OSError as error:
            observations.append({'seconds': elapsed, 'inventory_error': str(error)})
            previous = None
        else:
            last = actual
            locks = [name for name in actual if name.endswith('.lpr')]
            available = NATIVE.is_dir() and bool(actual)
            observations.append({'seconds': elapsed, 'complete_inventory': actual, 'lock_paths': locks,
                                 'native_directory_and_files_available': available})
            if available and not locks and actual == previous:
                return actual, {'settled': True, 'limit_seconds': 10, 'filtered_paths': [],
                                'observations': observations}
            previous = actual if available and not locks else None
        if time.monotonic() - started >= 10:
            return last, {'settled': False, 'limit_seconds': 10, 'filtered_paths': [],
                          'observations': observations}
        time.sleep(.5)


def check_completed(mode):
    out = E / ('read-v3r6-' + mode)
    result = load(out / 'execution.json')
    require(result['exit'] == 0 and not result.get('stopped_by_monitor'), 'previous phase failed/stopped: ' + mode)
    require(load(out / 'phase-review.json')['passed'], 'previous phase post-check did not pass: ' + mode)
    return out


def verify_postroute_runtime(out):
    boundary = {}
    for label in ['before-opt', 'after-opt', 'after-jfm-hook']:
        raw = (out / ('postroute-' + label + '-checks.txt')).read_text().splitlines()
        require(raw == ['ROUTED_FULLY|1', 'ERRORS_IN_ROUTES|0'], 'r6 route-status boundary failed: ' + label)
        require((out / ('postroute-' + label + '-route-status.rpt')).stat().st_size > 0,
                'r6 full raw route-status report missing: ' + label)
        boundary[label] = {'ROUTED_FULLY': 1, 'ERRORS_IN_ROUTES': 0}
    expected = ['ORIGINAL_ROUTE_COMPLETED', 'ROUTE_STATUS|before-opt|1|0',
                'PHYS_OPT_BEGIN|' + ' '.join(POSTROUTE_PARAMETERS), 'PHYS_OPT_END',
                'ROUTE_STATUS|after-opt|1|0', 'JFM_ROUTE_POST_FIRST_CALL_BEGIN',
                'JFM_ROUTE_POST_FIRST_CALL_END', 'ROUTE_STATUS|after-jfm-hook|1|0']
    require((out / 'postroute-order.txt').read_text().splitlines() == expected,
            'r6 optimization/original-hook order differs or repeated')
    return {'boundaries': boundary, 'exact_order': expected, 'one_phys_opt_pass': True,
            'one_original_JFM_route_post_call': True, 'no_additional_route_pass': True}


def preserve_derived_outputs(out, before):
    records = {}
    for name, raw in before.items():
        current = (REF / name).read_bytes() if (REF / name).exists() else None
        row = {'path': str(REF / name), 'exists_before': raw is not None, 'exists_after': current is not None,
               'before_SHA256': hashlib.sha256(raw).hexdigest() if raw is not None else None,
               'after_SHA256': hashlib.sha256(current).hexdigest() if current is not None else None,
               'original_bytes_unchanged': raw == current}
        for label, value in [('before', raw), ('after', current)]:
            if value is not None:
                path = out / ('derived-' + label + '-' + name)
                with path.open('xb') as file:
                    file.write(value)
        records[name] = row
    save_new(out / 'derived-output-preservation.json', records)
    return records


def bit_context_verification(out):
    keys = {'same_inmemory_project_design', 'same_leaf_geometry_after_pre', 'exact_reference_XPR_opened',
            'DIRECTORY_dot', 'part_unchanged'}
    contexts = []
    for label in ['after_pre', 'after_post']:
        rows = (out / ('bit-context-' + label + '.txt')).read_text().splitlines()
        flags = dict(row.split('|', 1) for row in rows if not row.startswith('physical_context|'))
        require(set(flags) == keys and set(flags.values()) == {'true'}, 'bit hook context checks incomplete/failed')
        physical = [row.split('|', 1)[1] for row in rows if row.startswith('physical_context|')]
        require(len(physical) == 1, 'bit actual physical context missing')
        contexts.append(physical[0])
    require(contexts[0] == contexts[1], 'bit pre/post checkpoint context differs')
    actual = (out / 'hook-open-project.txt').read_text().splitlines()
    require(actual == ['path|' + (REF / 'fpai_demo_vivado.xpr').as_posix()], 'factory bit hook opened wrong XPR')
    before = (out / 'bit-leaf-geometry-before_pre.txt').read_bytes()
    require(before and before == (out / 'bit-leaf-geometry-after_pre.txt').read_bytes()
            == (out / 'bit-leaf-geometry-after_post.txt').read_bytes(), 'bit leaf geometry evidence differs')
    return {key: True for key in sorted(keys)}


def bit_derived_verification(out, bit_proof):
    plan = bit_proof['factory_derived_isolation_plan']
    preserved = load(out / 'derived-output-preservation.json')
    writes = [row.split('|') for row in (out / 'factory-derived-writes.txt').read_text().splitlines()]
    require(len(writes) == 2 and all(len(row) == 3 and row[2] in {'w', 'wb'} for row in writes),
            'factory derived writes are incomplete or use unreviewed modes')
    outputs = {}
    for name, binding in plan['outputs'].items():
        before_after = preserved[name]
        require(before_after['original_bytes_unchanged'] and before_after['exists_before'] == binding['original_exists_before']
                and before_after['before_SHA256'] == before_after['after_SHA256'] == binding['original_before_SHA256'],
                'original factory derived-output path changed: ' + name)
        redirected = Path(binding['redirected_path'])
        require(redirected.resolve() == (out / 'factory-derived' / name).resolve()
                and redirected.is_file() and redirected.stat().st_size > 0, 'redirected factory output missing: ' + name)
        matches = [row for row in writes if Path(row[0]).resolve() == Path(binding['original_path']).resolve()
                   and Path(row[1]).resolve() == redirected.resolve()]
        require(len(matches) == 1, 'factory derived write target/count differs: ' + name)
        outputs[name] = {'original_path': binding['original_path'], 'redirected_path': str(redirected),
                         'original_protected': binding['original_protected'],
                         'original_before_SHA256': before_after['before_SHA256'],
                         'original_after_SHA256': before_after['after_SHA256'], 'original_bytes_unchanged': True,
                         'redirected_bytes': redirected.stat().st_size, 'redirected_SHA256': sha(redirected), 'write_count': 1}
    # The wrapper rejects either generated entry's basename before any exec.
    # Their raw contents remain factory output; neither is an execution entry.
    attempts = (out / 'factory-exec-attempts.txt').read_text().lower()
    require(not any(stem in attempts for stem in ['call_procise_disable_icap', 'procise_run_disable_icap']),
            'attempted execution of an archived raw factory entry')
    result = {'policy': plan['policy'], 'original_sources_unchanged': True,
              'raw_batch_executed': False, 'outputs': outputs}
    path = out / 'factory-derived-isolation.json'
    save_new(path, result)
    return {'path': str(path), 'SHA256': sha(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['bootstrap', 'route', 'reports', 'bit'])
    parser.add_argument('--check-only', action='store_true', help='read identities/build Tcl only; no directories or EDA')
    args = parser.parse_args()
    require(args.mode != 'bit', 'r6 bit is disabled; a failed or absent r6 routed gate cannot release it')
    driver_bytes = Path(__file__).read_bytes()
    driver_sha = hashlib.sha256(driver_bytes).hexdigest()
    proof = preflight()
    bit_proof = bit_preflight(proof) if args.mode == 'bit' else None
    tcl = build_tcl(args.mode)
    if args.check_only:
        print(json.dumps({'check_only': True, 'EDA_started': False, 'source_count': len(proof['source_sha256']),
                          'installed_count': len(proof['installed_sha256']), 'mode': args.mode,
                          'native_directory': str(NATIVE), 'Tcl_bytes': len(tcl.encode())}, indent=2))
        return
    stage = 'read-v3r6-' + args.mode
    out = E / stage
    require(not out.exists() and not (W / stage).exists(), 'phase output/work already exists; preserve it')
    if args.mode == 'bootstrap':
        require(not NATIVE.exists(), 'native checkpoint continuation directory already exists')
        NATIVE.mkdir()
        save_new(NATIVE / 'bootstrap-owner.json', {'native_directory': str(NATIVE),
                 'checkpoint_SHA256': CHECKPOINT_SHA, 'proof': proof, 'driver_SHA256': driver_sha})
    else:
        previous = check_completed('bootstrap' if args.mode == 'route' else 'reports' if args.mode == 'bit' else 'route')
        require(native_inventory() == load(previous / 'native-after.json'), 'native files changed or foreign files appeared')
        if args.mode == 'route':
            require(load(NATIVE / 'bootstrap-owner.json')['proof'] == proof, 'bootstrap identity proof changed')
        else:
            require(sha(ROUTED) == load(ROUTED_SHA_FILE)['SHA256'], 'new routed checkpoint identity changed')
        save_new(NATIVE / (args.mode + '-owner.json'), {'stage': stage, 'driver_SHA256': driver_sha,
                 'checkpoint_SHA256': CHECKPOINT_SHA, 'prior_native_manifest_SHA256': sha(previous / 'native-after.json')})
    spec = importlib.util.spec_from_file_location('checkpoint_owned_stage', Path(__file__).with_name('eda_owned_stage.py'))
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    owner.E, owner.W = E, W
    derived_before = {name: (REF / name).read_bytes() if (REF / name).exists() else None
                      for name in DERIVED_NAMES} if args.mode == 'bit' else {}
    try:
        owner.stage(stage, tcl, ceiling=180 if args.mode == 'bootstrap' else 1800 if args.mode == 'route' else 540,
                    run_names=['route_read_v3r6'])
    finally:
        if out.exists():
            (out / 'actual-driver.py').write_bytes(driver_bytes)
            save_new(out / 'input-proof.json', proof)
            snapshot, settling = settled_native_inventory()
            save_new(out / 'native-settling.json', settling)
            if snapshot is not None:
                save_new(out / 'native-after.json', snapshot)
            if bit_proof:
                save_new(out / 'bit-input-proof.json', bit_proof)
                preserve_derived_outputs(out, derived_before)
    require(load(out / 'native-settling.json')['settled'], 'owned EDA exited but full native inventory did not settle')
    require(preflight() == proof, 'source/toolchain/checkpoint identity changed during phase')
    spec = importlib.util.spec_from_file_location('checkpoint_gate_helpers', Path(__file__).with_name('review_ai_read_constraints.py'))
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    gate = load(GATE)
    indices = helpers.parse_indices((out / 'checkpoint-binding.txt').read_text(), 'source', 'capture')
    require(indices == gate['read_indices'], 'restored checkpoint source/capture indices differ from accepted gate')
    endpoint_name = 'read-snapshot-endpoints.txt' if args.mode == 'reports' else 'checkpoint-endpoints.txt'
    endpoints = helpers.snapshot_endpoints(out / endpoint_name, indices)
    clocks = helpers.clock_taps(out / 'clock-taps.txt', indices)
    if args.mode == 'route':
        require(ROUTED.exists() and (NATIVE / '.route_design.end.rst').exists(), 'actual routing completion missing')
        postroute_checks = verify_postroute_runtime(out)
        save_new(ROUTED_SHA_FILE, {'path': str(ROUTED), 'SHA256': sha(ROUTED), 'bytes': ROUTED.stat().st_size,
                 'source_physical_checkpoint_SHA256': CHECKPOINT_SHA, 'route_pass_not_final_acceptance': True})
    bit_identity_path = out / 'bit-identity.json'
    if args.mode == 'bit':
        require(bit_preflight(proof) == bit_proof, 'bit source/review/checkpoint/hook identity changed during phase')
        require(BIT.is_file() and BIT.stat().st_size > 0 and (NATIVE / '.write_bitstream.end.rst').is_file()
                and not (NATIVE / '.write_bitstream.error.rst').exists(), 'actual full native bit phase incomplete')
        context = bit_context_verification(out)
        derived = bit_derived_verification(out, bit_proof)
        save_new(bit_identity_path, {'path': str(BIT), 'bytes': BIT.stat().st_size, 'SHA256': sha(BIT),
                 'source_routed_checkpoint_SHA256': bit_proof['source_routed_checkpoint_SHA256'],
                 'source_physical_checkpoint_SHA256': CHECKPOINT_SHA,
                 'formal_routed_review_SHA256': bit_proof['formal_routed_review_SHA256'],
                 'factory_hook_SHA256': bit_proof['factory_hook_SHA256'], 'context_verification': context,
                 'factory_derived_isolation': derived})
    phase_review = {'passed': True, 'scope': 'this offline phase only; final routed gates remain required',
             'mode': args.mode, 'source_identity_unchanged': True, 'read_bits': len(indices),
             'restored_snapshot_endpoint_bound': endpoints, 'actual_clocks': clocks,
             'no_managed_run_status_used_or_fabricated': True, 'new_BOOT_reboot_permission': False,
             'bit_generation_implemented': args.mode == 'bit'}
    if args.mode == 'bit':
        phase_review.update({'candidate_run': 'route_read_v3r6', 'managed_run': False,
                             'bit_identity_path': str(bit_identity_path)})
    if args.mode == 'route':
        phase_review['postroute_order_checks'] = postroute_checks
    save_new(out / 'phase-review.json', phase_review)
    print(json.dumps({'phase': stage, 'passed': True, 'scope': 'phase only; no board acceptance'}))


if __name__ == '__main__':
    main()
