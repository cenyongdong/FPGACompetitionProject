"""Fresh r7 project flow. Default inspect is read-only; explicit stages run EDA.

No bit/ICAP/BOOT/remote/device entry point exists. Each stage owns one bounded
Vivado process using the unchanged owned-CPU supervisor and original hooks.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import importlib.util
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
START_DRIVER_BYTES = Path(__file__).read_bytes()
START_DRIVER_SHA256 = hashlib.sha256(START_DRIVER_BYTES).hexdigest()
R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-live-20261017-r7'
E = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r7'
REF = W / 'reference'
E3 = R / 'tools/pose-v1/evidence/hdmi-live-20261017-r3'
PREPARATION = E / 'preparation/review.json'
SAFETY = E / 'preparation-safety-r2/review.json'
TOOL = Path('D:/vivado18.3/Vivado/2018.3')
MANAGED = E3 / 'managed-PS-observer-r2/review.json'
PS_REL = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v'
BD_REL = 'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd'
WRAPPER_REL = 'rtl/ps_ai_wrapper.sv'
SYNTH = 'synth_read_v3r7'
PREVIEW = 'synth_read_v3r7_preview_r2'
IMPL = 'impl_read_v3r7'
CACHE_POLICY = 'exact-24-gen-run-xml-mtime-only-v1'
FAILED_SETUP = E / 'setup-cache-failure-r1'
LEGACY = Path(__file__).with_name('continue_ai_monitor_candidate.py')
READ_DRIVER = Path(__file__).with_name('continue_ai_read_candidate.py')
SUPERVISOR = Path(__file__).with_name('eda_owned_stage.py')
FROZEN = {LEGACY: 'e30ffbe3fb4231096ab19f6423daaf39994c2427ed52a73086ca07da8cc06941',
          READ_DRIVER: 'a100884326b044a6c054e8331255135a4e1231a53ad5d86def5ecf208100b55d',
          SUPERVISOR: '3a098b066127c53d26bfb5829c253055fc796e7078888edb0a9ce21acdd2b672'}


def require(value, message):
    if not value:
        raise ValueError(message)


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def literal_values(path, name):
    values = []
    for node in ast.walk(ast.parse(path.read_bytes(), filename=str(path))):
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == name
                                               for target in node.targets):
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                values.append((node.lineno, node.value.value))
    return [value for _, value in sorted(values)]


def stage_name(mode):
    return 'read-v3r7-' + mode + ('-r2' if mode == 'setup' else '')


def cached_ooc_inventory():
    """Preserve byte identities and mtimes of caches that are never launch targets."""
    prep = load(PREPARATION)
    safety = load(SAFETY)
    require(safety['passed'] is True and safety['preparation_review_SHA256'] == sha(PREPARATION)
            and safety['ordinary_independent_destination_files'] == prep['copied_files']
            and safety['source_preparer_not_rerun'] is True,
            'Independent post-copy safety review missing/changed')
    inventory = {}
    for name in prep['OOC_cached_run_names']:
        base = REF / 'fpai_demo_vivado.runs' / name
        require(base.is_dir() and not base.is_symlink(), 'Cached OOC directory missing/nonordinary')
        for path in base.rglob('*'):
            require(not path.is_symlink(), 'Unexpected OOC symlink')
            if path.is_file():
                inventory[path.relative_to(REF).as_posix()] = {
                    'SHA256': sha(path), 'bytes': path.stat().st_size,
                    'mtime_ns': path.stat().st_mtime_ns}
    return inventory


def metadata_paths():
    names = load(PREPARATION)['OOC_cached_run_names']
    require(len(names) == len(set(names)) == 24
            and all(name.endswith('_synth_1') and '/' not in name and '\\' not in name for name in names),
            'Exact original 24 OOC names required')
    return sorted('fpai_demo_vivado.runs/' + name + '/gen_run.xml' for name in names)


def cache_difference(before, after):
    common = set(before) & set(after)
    return {'new_files': sorted(set(after)-set(before)), 'deleted_files': sorted(set(before)-set(after)),
            'byte_or_size_changed_files': sorted(p for p in common if before[p]['SHA256'] != after[p]['SHA256']
                                                 or before[p]['bytes'] != after[p]['bytes']),
            'mtime_changed_files': sorted(p for p in common if before[p]['mtime_ns'] != after[p]['mtime_ns'])}


def compare_ooc_cache(before, after, allowed):
    """Only exact original gen_run.xml mtimes may differ; all content stays fixed."""
    require(len(before) == len(after) == 451 and set(before) == set(after), 'Cached OOC file set changed')
    require(isinstance(allowed, list) and sorted(allowed) == metadata_paths()
            and len(allowed) == len(set(allowed)) == 24 and set(allowed) <= set(before),
            'Exact 24 cached metadata paths required')
    for relative in before:
        for record in [before[relative], after[relative]]:
            require(set(record) == {'SHA256', 'bytes', 'mtime_ns'}
                    and isinstance(record['SHA256'], str) and re.fullmatch('[0-9a-f]{64}', record['SHA256'])
                    and type(record['bytes']) is int and record['bytes'] >= 0
                    and type(record['mtime_ns']) is int and record['mtime_ns'] >= 0,
                    'Cached OOC inventory record invalid: ' + relative)
        require(before[relative]['SHA256'] == after[relative]['SHA256']
                and before[relative]['bytes'] == after[relative]['bytes'],
                'Cached OOC content changed: ' + relative)
        if relative not in allowed:
            require(before[relative]['mtime_ns'] == after[relative]['mtime_ns'],
                    'Nonmetadata OOC timestamp changed: ' + relative)
    changed = sorted(p for p in allowed if before[p]['mtime_ns'] != after[p]['mtime_ns'])
    return {'passed': True, 'policy': CACHE_POLICY, 'files_checked': 451,
            'metadata_paths': sorted(allowed), 'allowed_metadata_mtime_changes': changed,
            'other_files_mtime_unchanged': 427, 'all_files_content_and_set_unchanged': True,
            'difference': cache_difference(before, after)}


def failed_setup_context():
    failed = load(FAILED_SETUP / 'review.json')
    require(failed['capture_complete'] is True and failed['actual_phase_review_exists'] is False
            and not (E / 'read-v3r7-setup/phase-review.json').exists()
            and failed['old_protected_source_changes'] == failed['new_protected_source_changes']
            == failed['installed_library_changes'] == [] and failed['old_XPR_unchanged'] is True,
            'Original failed setup preservation missing or scope differs')
    snapshot = FAILED_SETUP / 'fpai_demo_vivado.xpr.after'
    expected = sha(snapshot)
    require(sha(REF / 'fpai_demo_vivado.xpr') == expected,
            'Current XPR differs from preserved failed setup, do not reset/retry')
    name = 'synth_read_v3r7_preview'
    entries = [run for run in ET.parse(snapshot).getroot().iter('Run') if run.get('Id') == name]
    require(len(entries) == 1 and entries[0].get('Dir') == '$PRUNDIR/' + name
            and entries[0].get('Type') == 'Ft3:Synth' and entries[0].get('SrcSet') == 'sources_1'
            and entries[0].get('ConstrsSet') == 'constrs_1'
            and entries[0].get('Part') == 'xc7z030ffg676-2', 'Failed preview XPR run identity differs')
    status = FAILED_SETUP / 'stage/preview-run-status.txt'
    require(status.read_text().strip() == 'name=' + name + '|status=Scripts Generated|needs_refresh=0',
            'Previous preview was not the preserved scripts-only state')
    base = REF / 'fpai_demo_vivado.runs' / name
    files = {path.relative_to(base).as_posix(): path for path in base.rglob('*') if path.is_file()}
    require(set(files) == set(failed['preview_files'])
            and not any(path.name == 'runme.log' or path.suffix == '.rst' for path in files.values()),
            'Previous preview gained execution files or changed its file set')
    for relative, path in files.items():
        identity = failed['preview_files'][relative]
        require(sha(path) == identity['SHA256'] and path.stat().st_size == identity['bytes'],
                'Previous scripts-only preview bytes changed: ' + relative)
    return {'initial_XPR_SHA256': expected, 'initial_XPR_source_path': str(snapshot),
            'predecessor_failed_setup_review_path': str(FAILED_SETUP / 'review.json'),
            'predecessor_failed_setup_review_SHA256': sha(FAILED_SETUP / 'review.json'),
            'predecessor_failed_setup_remains_failed': True,
            'prior_preview_status_path': str(status), 'prior_preview_status_SHA256': sha(status),
            'prior_preview_source_files': failed['preview_files'], 'prior_preview_not_executed': True}


def completed(mode):
    directory = E / stage_name(mode)
    result, review = load(directory / 'execution.json'), load(directory / 'phase-review.json')
    require(type(result['exit']) is int and result['exit'] == 0
            and result.get('stopped_by_monitor') is False and result.get('timeout', False) is False
            and review['passed'] is True and review['mode'] == mode,
            'Actual predecessor phase failed/missing: ' + mode)
    require(review['preparation_review_SHA256'] == sha(PREPARATION), 'Predecessor preparation changed')
    return directory


def preflight():
    require(sha(Path(__file__)) == START_DRIVER_SHA256, 'Driver source changed after process start')
    for path, value in FROZEN.items():
        require(sha(path) == value, 'Frozen public source changed: ' + str(path))
    prep = load(PREPARATION)
    require(prep['passed'] is True and prep['schema'] == 'hdmi-reader-idle-r7-preparation-v1'
            and prep['source_count'] == len(prep['source_sha256']) == 937
            and len(prep['path_migrations']) == 25, 'Fresh source preparation invalid')
    require(Path(prep['new_reference']).resolve() == REF.resolve(), 'New reference path differs')
    for relative, value in prep['source_sha256'].items():
        require(sha(REF / relative) == value, 'r7 source changed: ' + relative)
    for relative, value in prep['original_source_sha256'].items():
        require(sha(Path(prep['old_reference']) / relative) == value, 'Original source changed: ' + relative)
    old_xpr = Path(prep['old_reference']) / 'fpai_demo_vivado.xpr'
    require(sha(old_xpr) == prep['xpr']['before_SHA256'], 'Original XPR changed')
    require(len(prep['installed_sha256']) == 41, 'Installed file count differs')
    for relative, value in prep['installed_sha256'].items():
        require(sha(TOOL / relative) == value, 'Installed library changed: ' + relative)
    require(sha(MANAGED) == prep['managed_PS_receipt_SHA256'], 'Managed source receipt changed')
    require(sha(REF / PS_REL) == 'b87b798ce01c707027766660c501ed2232aaeaec5f093bc291e095ab1f637cb7'
            and sha(REF / WRAPPER_REL) == '502c463544a5cbc4e5af20460af274418e5f6c68661e92ee6a3eca9c8b3c86f2',
            'Managed full PS/wrapper regenerated or renamed')
    tree = ET.parse(REF / 'fpai_demo_vivado.xpr').getroot()
    require(tree.attrib['Path'].lower() == (REF / 'fpai_demo_vivado.xpr').as_posix().lower(),
            'Current XPR belongs to another reference')
    require(all(p.get('Path', '').startswith(('$PPRDIR/', '$PSRCDIR/')) for p in tree.iter('File')),
            'Absolute/nonlocal XPR file registration')
    for run in tree.iter('Run'):
        if run.get('Id') == IMPL:
            require(run.get('SynthRun') == SYNTH, 'XPR implementation has the wrong synthesis parent')
    return {'preparation_review_path': str(PREPARATION), 'preparation_review_SHA256': sha(PREPARATION),
            'source_safety_review_path': str(SAFETY), 'source_safety_review_SHA256': sha(SAFETY),
            'source_sha256': prep['source_sha256'], 'original_source_sha256': prep['original_source_sha256'],
            'installed_identity_ledger_SHA256': prep['installed_identity_ledger_SHA256'],
            'installed_sha256': prep['installed_sha256'], 'managed_PS_receipt_SHA256': sha(MANAGED),
            'original_XPR_SHA256': sha(old_xpr),
            'driver_SHA256': START_DRIVER_SHA256, 'supervisor_SHA256': sha(SUPERVISOR),
            'algorithm_source_SHA256': {str(p): value for p, value in FROZEN.items()},
            'candidate_run': IMPL, 'managed_run': True, 'parent_synthesis': SYNTH,
            'RTL_functional_change_count': 1, 'extra_r6_postroute_optimization': False,
            'new_timing_or_DRC_waiver': False}


COMMON = r'''
proc check_managed_ps {} {
 foreach {actual expected} {
  {@@REF@@/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v} {@@OLD_E@@/managed-PS-observer-r2/ps_ai.v.after}
  {@@REF@@/rtl/ps_ai_wrapper.sv} {@@OLD_E@@/managed-PS-observer-r2/ps_ai_wrapper.sv.after}
 } {
  set f [open $actual r];fconfigure $f -translation binary;set a [read $f];close $f
  set f [open $expected r];fconfigure $f -translation binary;set b [read $f];close $f
  if {$a ne $b} {error "Managed passive PS output regenerated/changed: $actual"}
 }
}
proc audit_dependencies {} {
 check_managed_ps
 if {[file normalize [get_property DIRECTORY [current_project]]] ne [file normalize {@@REF@@}]} {error "Wrong project directory"}
 if {[get_property PART [current_project]] ne "xc7z030ffg676-2"} {error "Wrong target part"}
 set bd [get_files -quiet {@@REF@@/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}]
 if {[llength $bd]!=1} {error "Original managed BD absent/duplicate"}
 update_compile_order -fileset sources_1
 set files [get_files -compile_order sources -used_in synthesis]
 set f [open {@@OUT@@/source-order.txt} w];foreach file $files {puts $f $file};close $f
 foreach tail {ps_ai_read_observed.v ps_ai_original_submodules.v} {
  foreach file $files {if {[file tail $file] eq $tail} {error "Inactive split PS became compiled: $tail"}}
 }
 foreach tail {ps_ai.v ps_ai_wrapper.sv} {
  set n 0;foreach file $files {if {[file tail $file] eq $tail} {incr n}}
  if {$n!=1} {error "Managed full PS definition not unique: $tail $n"}
 }
 foreach name {proc_sys_reset_0_1 util_vector_logic_0_0 processing_system7_0_0 xbar_0 xbar_1 proc_sys_reset_0_0 xbar_4 s00_regslice_0 s00_regslice_1 s01_regslice_0 m00_regslice_0} {
  set expected [file normalize "@@REF@@/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ip/ps_ai_$name/ps_ai_$name.dcp"]
  set n 0;foreach file $files {if {[file normalize $file] eq $expected} {incr n}}
  if {$n!=1} {error "Managed PS leaf DCP not unique: $name $n"}
 }
 set f [open {@@OUT@@/OOC-state.txt} w]
 foreach name {@@OOC@@} {
  set run [get_runs -quiet $name]
  if {[llength $run]!=1} {error "Protected OOC absent: $name"}
  set status [get_property STATUS $run];set refresh [get_property NEEDS_REFRESH $run]
  puts $f "$name|$status|$refresh"
  if {$status ne "synth_design Complete!" || $refresh} {error "Cached OOC stale; do not regenerate: $name"}
 }
 close $f
 foreach ip [get_ips -all] {if {[get_property IS_LOCKED $ip]} {error "Original IP unexpectedly locked: $ip"}}
 check_managed_ps
}
proc inherit_hooks {old new} {
 foreach p [list_property $old] {
  if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
   set val [get_property $p $old]
   if {$val ne ""} {
    if {![string equal -nocase [string range [file normalize $val] 0 [expr {[string length [file normalize {@@REF@@}]]-1}]] [file normalize {@@REF@@}]]} {error "Nonlocal hook $p $val"}
    set_property $p $val $new
   }
  }
 }
}
'''

SETUP = r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
if {[llength [get_runs -quiet synth_read_v3r7]] || [llength [get_runs -quiet impl_read_v3r7]]} {error "Preserve existing r7 top runs"}
audit_dependencies
check_syntax -fileset sources_1
report_ip_status -file {@@OUT@@/IP-status.rpt}
if {[llength [get_runs -quiet synth_read_v3r7_preview_r2]]} {error "Preserve existing preview scripts"}
set old [get_runs synth_1]
create_run synth_read_v3r7_preview_r2 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
set nr [get_runs synth_read_v3r7_preview_r2]
inherit_hooks $old $nr
launch_runs synth_read_v3r7_preview_r2 -scripts_only
set f [open {@@OUT@@/preview-run-status.txt} w]
puts $f "name=$nr|status=[get_property STATUS $nr]|needs_refresh=[get_property NEEDS_REFRESH $nr]"
close $f
audit_dependencies
close_project
puts "HDMI_READER_R7_SETUP_COMPLETE_NOT_SYNTHESIZED"
'''

SYNTHESIS = r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
audit_dependencies
if {[llength [get_runs -quiet synth_read_v3r7]]} {error "Preserve previous r7 synthesis"}
set old [get_runs synth_1]
create_run synth_read_v3r7 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
set nr [get_runs synth_read_v3r7]
inherit_hooks $old $nr
current_run -synthesis $nr
launch_runs synth_read_v3r7 -jobs 1
wait_on_run synth_read_v3r7
if {[get_property STATUS $nr] ne "synth_design Complete!" || [get_property NEEDS_REFRESH $nr]} {error "Fresh synthesis incomplete/stale"}
audit_dependencies
open_run synth_read_v3r7
write_checkpoint {@@OUT@@/ai-read-synth-v3.dcp}
report_utilization -file {@@OUT@@/utilization.rpt}
close_project
puts "HDMI_READER_R7_SYNTHESIS_COMPLETE_NOT_ROUTED"
'''

PLACE = r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
audit_dependencies
set sr [get_runs synth_read_v3r7]
if {[get_property STATUS $sr] ne "synth_design Complete!" || [get_property NEEDS_REFRESH $sr]} {error "Fresh synthesis incomplete/stale"}
if {[llength [get_runs -quiet impl_read_v3r7]]} {error "Preserve previous r7 implementation"}
set old [get_runs impl_1]
create_run impl_read_v3r7 -parent_run synth_read_v3r7 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
set nr [get_runs impl_read_v3r7]
inherit_hooks $old $nr
set_property STEPS.OPT_DESIGN.TCL.PRE {@@REF@@/ip_patch/process_control/implementation_opt_pre_hdmi.tcl} $nr
set f [open {@@OUT@@/implementation-profile.txt} w]
foreach p {FLOW STRATEGY CONSTRSET PART STEPS.PLACE_DESIGN.ARGS.DIRECTIVE STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED} {puts $f "$p|[get_property $p $nr]"}
foreach p [list_property $nr] {if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {puts $f "$p|[get_property $p $nr]"}}
close $f
if {[get_property STRATEGY $nr] ne "Performance_NetDelay_high"
 || [get_property STEPS.PLACE_DESIGN.ARGS.DIRECTIVE $nr] ne "ExtraNetDelay_high"
 || [get_property STEPS.PHYS_OPT_DESIGN.ARGS.DIRECTIVE $nr] ne "AggressiveExplore"
 || [get_property STEPS.ROUTE_DESIGN.ARGS.DIRECTIVE $nr] ne "NoTimingRelaxation"
 || [get_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED $nr]} {error "Original factory implementation profile changed"}
current_run -implementation $nr
launch_runs impl_read_v3r7 -to_step phys_opt_design -jobs 1
wait_on_run impl_read_v3r7
if {[get_property STATUS $nr] ne "phys_opt_design Complete!" || [get_property NEEDS_REFRESH $nr]} {error "Fresh place/physopt incomplete/stale"}
audit_dependencies
open_run impl_read_v3r7
write_checkpoint {@@OUT@@/ai7030_edif_top_physopt.dcp}
report_timing_summary -file {@@OUT@@/placed-timing-summary.rpt}
close_project
puts "HDMI_READER_R7_NEW_PHYSOPT_CHECKPOINT_COMPLETE_NOT_ROUTED"
'''

ROUTE = r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
audit_dependencies
set nr [get_runs impl_read_v3r7]
if {[get_property STATUS $nr] ne "phys_opt_design Complete!" || [get_property NEEDS_REFRESH $nr]} {error "Only this new completed physical stage may continue"}
launch_runs impl_read_v3r7 -to_step route_design -jobs 1
wait_on_run impl_read_v3r7
if {[get_property STATUS $nr] ne "route_design Complete!" || [get_property NEEDS_REFRESH $nr]} {error "Fresh route incomplete/stale"}
audit_dependencies
open_run impl_read_v3r7
write_checkpoint {@@OUT@@/ai-read-routed.dcp}
report_route_status -file {@@OUT@@/route-status.rpt}
close_project
puts "HDMI_READER_R7_ROUTED_NOT_REVIEWED_NO_BITSTREAM"
'''


def build_tcl(mode):
    prep = load(PREPARATION)
    endpoints = literal_values(READ_DRIVER, 'endpoint_proc')
    extra = literal_values(READ_DRIVER, 'extra')
    constraints = literal_values(READ_DRIVER, 'body')
    old = literal_values(LEGACY, 'body')
    require(len(endpoints) == len(extra) == len(constraints) == 1 and len(old) == 5,
            'Frozen original Tcl extraction differs')
    # Use only its unchanged endpoint helper; managed checks above remain exact.
    endpoint = endpoints[0].split('proc ai_read_dump_endpoints', 1)
    require(len(endpoint) == 2, 'Endpoint helper missing/ambiguous')
    endpoint = 'proc ai_read_dump_endpoints' + endpoint[1]
    if mode == 'setup':
        body = SETUP
    elif mode == 'synthesis':
        body = SYNTHESIS
    elif mode == 'place':
        body = PLACE
    elif mode == 'route':
        body = ROUTE
    elif mode == 'constraints':
        body = constraints[0].replace('synth_read_v3r3', SYNTH)
        body = body.replace('close_project', 'audit_dependencies\nclose_project')
    elif mode == 'reports':
        body = old[3].replace('impl_ai_monitor_v2', IMPL)
        require(body.count('close_project') == 1, 'Report body close boundary differs')
        body = body.replace('close_project', extra[0] + '\naudit_dependencies\nclose_project')
        body = body.replace('ai-monitor-routed.dcp', 'ai-read-routed.dcp')
    else:
        raise ValueError('No bit/device stage exists')
    common = COMMON.replace('@@OLD_E@@', E3.as_posix()).replace(
        '@@OOC@@', ' '.join(prep['OOC_cached_run_names']))
    return ('if {[catch {\nsource {@@REF@@/ip_patch/project_execution_guard.tcl}\n'
            + common + '\n' + endpoint + '\ncheck_managed_ps\n'
            + body + '\n} result]} {puts "HDMI_READER_R7_STAGE_FAILED $result";puts $::errorInfo;exit 1}\nexit\n')


def native_identity(mode):
    run = PREVIEW if mode == 'setup' else (SYNTH if mode == 'synthesis' else IMPL)
    path = REF / f'fpai_demo_vivado.runs/{run}/ai7030_edif_top.tcl'
    raw = path.read_text(encoding='utf-8').replace('\\', '/')
    require('hdmi-live-20261017-r3' not in raw and 'hdmi-jfm-build-20261016-r1' not in raw,
            'New top native Tcl retained an old workspace reference')
    allowed = [REF.as_posix().lower() + '/', TOOL.as_posix().lower() + '/']
    absolute = re.findall(r'[A-Za-z]:/[^\s{}\"\[\];)\r\n]+', raw)
    require(all('..' not in Path(value).parts
                and any(value.lower().startswith(base) for base in allowed)
                and (Path(value).resolve().is_relative_to(REF.resolve())
                     or Path(value).resolve().is_relative_to(TOOL.resolve())) for value in absolute),
            'New top native Tcl has an unreviewed absolute source/context path')
    result = {'path': str(path), 'SHA256': sha(path), 'absolute_paths_checked': len(absolute),
              'only_new_REF_or_fixed_toolchain': True,
              'OOC_cached_scripts_execution_policy': 'forbidden; cache bytes and mtimes compared separately'}
    if mode in ('setup', 'synthesis'):
        lines = [line.strip().lower() for line in raw.splitlines()]
        expected = ('add_files ' + (REF / BD_REL).as_posix()).lower()
        require(lines.count(expected) == 1, 'Actual new native synth does not add original BD uniquely')
        result['actual_BD_add_files_line'] = expected
    else:
        for command in ['place_design -directive ExtraNetDelay_high',
                        'phys_opt_design -directive AggressiveExplore',
                        'route_design -directive NoTimingRelaxation']:
            require(sum(line.strip() == command for line in raw.splitlines()) == 1,
                    'Original implementation command missing/duplicated: ' + command)
        require('phys_opt_design -placement_opt' not in raw, 'r6 postroute optimization leaked into r7')
    return result


def file_identity(path):
    require(path.is_file() and path.stat().st_size > 0, 'Actual checkpoint missing: ' + str(path))
    return {'path': str(path), 'bytes': path.stat().st_size, 'SHA256': sha(path)}


def preview_equivalence(actual_path):
    frozen = E / stage_name('setup') / 'preview-native.tcl'
    preview_record = load(E / stage_name('setup') / 'preview-native-identity.json')
    require(sha(frozen) == preview_record['SHA256']
            and sha(Path(preview_record['path'])) == preview_record['SHA256'],
            'Reviewed never-executed preview changed')
    before, after = frozen.read_bytes(), actual_path.read_bytes()
    old, new = PREVIEW.encode('ascii'), SYNTH.encode('ascii')
    positions = [m.start() for m in re.finditer(re.escape(old), before)]
    require(positions and before.count(new) == len(positions), 'Unexpected synthesis-name occurrence')
    changed = before.replace(old, new)
    require(changed == after and after.count(new) == len(positions)
            and after.replace(new, old) == before, 'Actual native differs beyond exact run-name migration')
    return {'passed': True, 'preview_path': str(frozen), 'preview_SHA256': sha(frozen),
            'actual_path': str(actual_path), 'actual_SHA256': sha(actual_path),
            'old_run': PREVIEW, 'new_run': SYNTH, 'substitution_count': len(positions),
            'old_positions': positions, 'inverse_byte_exact': True,
            'preview_scripts_only_not_synthesis_pass': True}


def run(mode):
    proof = preflight()
    frozen_inputs = {path: path.read_bytes() for path in FROZEN}
    cached_before = cached_ooc_inventory()
    proof['OOC_cached_files_before'] = cached_before
    allowed = metadata_paths()
    proof['OOC_cache_policy'] = CACHE_POLICY
    proof['OOC_metadata_expected_paths'] = allowed
    metadata_before = {relative: (REF / relative).read_bytes() for relative in allowed}
    if mode == 'setup':
        proof.update(failed_setup_context())
    else:
        previous = {'synthesis': 'setup', 'constraints': 'synthesis', 'place': 'constraints',
                    'route': 'place', 'reports': 'route'}[mode]
        completed(previous)
    if mode == 'synthesis':
        snapshot = E / stage_name('setup') / 'fpai_demo_vivado.xpr'
        identity = load(snapshot.with_name('xpr-after-setup.json'))
        require(sha(snapshot) == identity['sha256'] == sha(REF / 'fpai_demo_vivado.xpr'),
                'Fresh synthesis must inherit the exact completed setup-r2 XPR')
        proof['initial_XPR_source_path'] = str(snapshot)
        proof['initial_XPR_SHA256'] = sha(snapshot)
    if mode in ('place', 'route'):
        gate = load(E / stage_name('constraints') / 'review.json')
        require(gate['route_prerequisite_pass'] is True and gate['read_bits'] == 2768,
                'Actual fresh r7 constraint gate required')
        require(gate['source_sha256'] == proof['source_sha256'], 'Constraint source ledger differs')
        proof['constraint_review_SHA256'] = sha(E / stage_name('constraints') / 'review.json')
    parent_checkpoint = None
    if mode in ('place', 'route'):
        predecessor = 'synthesis' if mode == 'place' else 'place'
        parent_checkpoint = load(E / stage_name(predecessor) / 'phase-artifacts.json')['native_checkpoint']
        require(file_identity(Path(parent_checkpoint['path'])) == parent_checkpoint,
                'Actual new parent native checkpoint changed')
        proof['parent_checkpoint'] = parent_checkpoint
    tcl = build_tcl(mode)
    spec = importlib.util.spec_from_file_location('r7_owned_supervisor', SUPERVISOR)
    supervisor = importlib.util.module_from_spec(spec); spec.loader.exec_module(supervisor)
    supervisor.E, supervisor.W = E, W
    directory = E / stage_name(mode)
    cached_after, comparison = None, None
    try:
        out = supervisor.stage(stage_name(mode), tcl, ceiling=1800 if mode in ('synthesis', 'place', 'route') else 540,
                               run_names=[SYNTH] if mode in ('synthesis', 'constraints') else ([IMPL] if mode != 'setup' else []))
    finally:
        if directory.exists():
            (directory / 'actual-driver.py').write_bytes(START_DRIVER_BYTES)
            save(directory / 'input-proof.json', proof)
            save(directory / 'OOC-cache-before.json', cached_before)
            for path, raw in frozen_inputs.items():
                (directory / ('input-' + path.name)).write_bytes(raw)
            for relative, raw in metadata_before.items():
                target = directory / 'OOC-metadata-before' / relative
                target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(raw)
            try:
                cached_after = cached_ooc_inventory()
                save(directory / 'OOC-cache-after.json', cached_after)
                for relative in allowed:
                    source = REF / relative
                    if source.is_file():
                        target = directory / 'OOC-metadata-after' / relative
                        target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(source.read_bytes())
                comparison = compare_ooc_cache(cached_before, cached_after, allowed)
            except Exception as error:
                comparison = {'passed': False, 'policy': CACHE_POLICY,
                              'error': type(error).__name__ + ': ' + str(error),
                              'difference': cache_difference(cached_before, cached_after) if cached_after is not None else None}
            save(directory / 'OOC-cache-comparison.json', comparison)
    preflight()
    require(comparison is not None and comparison['passed'] is True,
            'Cached OOC invariant failed; preserve inventory/comparison and stop')
    xpr = REF / 'fpai_demo_vivado.xpr'
    shutil.copyfile(xpr, out / 'fpai_demo_vivado.xpr')
    identity = {'sha256': sha(xpr), 'path': str(xpr), 'managed_source_review': str(MANAGED),
                'managed_source_review_sha256': sha(MANAGED), 'PS_output_SHA256': sha(REF / PS_REL),
                'source_preparation_review_sha256': sha(PREPARATION)}
    save(out / ('xpr-after-setup.json' if mode == 'setup' else 'xpr-identity.json'), identity)
    actual_native = native_identity(mode) if mode in ('setup', 'synthesis', 'place', 'route') else None
    if actual_native:
        shutil.copyfile(Path(actual_native['path']), out / 'actual-native.tcl')
        shutil.copyfile(Path(actual_native['path']), out / 'native-script.tcl')
        save(out / 'native-source-identity.json', actual_native)
        if mode == 'setup':
            shutil.copyfile(Path(actual_native['path']), out / 'preview-native.tcl')
            save(out / 'preview-native-identity.json', actual_native)
        if mode == 'synthesis':
            save(out / 'preview-actual-equivalence.json', preview_equivalence(Path(actual_native['path'])))
    checkpoint = {'synthesis': 'ai-read-synth-v3.dcp', 'place': 'ai7030_edif_top_physopt.dcp',
                  'route': 'ai-read-routed.dcp', 'reports': 'ai-read-routed.dcp'}.get(mode)
    dcp = None
    if checkpoint:
        path = out / checkpoint
        require(path.is_file() and path.stat().st_size > 0, 'Actual new checkpoint absent')
        dcp = {'path': str(path), 'bytes': path.stat().st_size, 'SHA256': sha(path)}
        save(out / 'checkpoint-identity.json', dcp)
    native_checkpoint = None
    if mode in ('synthesis', 'place', 'route'):
        native_run = SYNTH if mode == 'synthesis' else IMPL
        native_name = {'synthesis': 'ai7030_edif_top.dcp', 'place': 'ai7030_edif_top_physopt.dcp',
                       'route': 'ai7030_edif_top_routed.dcp'}[mode]
        native_checkpoint = file_identity(REF / 'fpai_demo_vivado.runs' / native_run / native_name)
    save(out / 'phase-artifacts.json', {'mode': mode, 'native': actual_native,
                                      'checkpoint': dcp, 'native_checkpoint': native_checkpoint,
                                      'parent_checkpoint': parent_checkpoint, 'candidate_run': IMPL,
                                      'parent_synthesis': SYNTH, 'managed_run': True})
    save(out / 'phase-review.json', {'passed': True, 'mode': mode,
         'preparation_review_SHA256': sha(PREPARATION), 'source_count': 937, 'installed_count': 41,
         'managed_PS_OOC_count': 11, 'OOC_cached_count': 24,
         'native': actual_native, 'checkpoint': dcp, 'candidate_run': IMPL, 'managed_run': True,
         'parent_synthesis': SYNTH, 'source_identity_unchanged_after_this_phase': True,
         'OOC_cache_content_and_set_unchanged': True,
         'OOC_cache_nonmetadata_mtimes_unchanged': True,
         'OOC_metadata_mtime_policy': CACHE_POLICY,
         'OOC_cache_comparison_SHA256': sha(out / 'OOC-cache-comparison.json'),
         'extra_r6_postroute_optimization': False, 'new_timing_or_DRC_waiver': False,
         'board_executed': False, 'bit_generation_implemented': False})
    print(json.dumps({'passed': True, 'mode': mode, 'evidence': str(out), 'board_executed': False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', nargs='?', default='inspect',
                        choices=['inspect', 'setup', 'synthesis', 'constraints', 'place', 'route', 'reports'])
    args = parser.parse_args()
    if args.mode == 'inspect':
        proof = preflight()
        for mode in ['setup', 'synthesis', 'constraints', 'place', 'route', 'reports']:
            require('generate_target' not in build_tcl(mode), 'Unexpected IP regeneration')
        print(json.dumps({'ready': True, 'read_only': True, 'source_count': len(proof['source_sha256']),
                          'installed_count': len(proof['installed_sha256']), 'EDA_executed': False,
                          'board_executed': False, 'bit_generation_implemented': False}))
    else:
        run(args.mode)


if __name__ == '__main__':
    main()
