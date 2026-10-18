"""Staged offline v3 build. Reuse reviewed v2 Tcl, without executing its driver.

Each invocation owns exactly one fresh EDA stage. No board access is provided.
"""
from pathlib import Path
import hashlib,importlib.util,json,re,sys,shutil

R=Path(__file__).resolve().parents[3]
W=R/'.local/hdmi-live-20261017-r3'
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r3'
spec=importlib.util.spec_from_file_location('eda_support',Path(__file__).with_name('eda_owned_stage.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.E=E;m.W=W
mode=sys.argv[1]
assert mode in ('synthesis','constraints','route','reports','bit')
assert json.loads((E/'read-candidate-preparation/review.json').read_text())['passed']
legacy=Path(__file__).with_name('continue_ai_monitor_candidate.py')
assert hashlib.sha256(legacy.read_bytes()).hexdigest()=='e30ffbe3fb4231096ab19f6423daaf39994c2427ed52a73086ca07da8cc06941'
bodies=re.findall(r"body=r'''(.*?)'''",legacy.read_text(),re.S)
assert len(bodies)==5

def stage_name(name):
    return ('read-v3r3-' if name in ('synthesis','constraints') else 'read-v3r4-')+name+('-r3' if name=='constraints' else '')

def complete(name):
    assert json.loads((E/stage_name(name)/'execution.json').read_text())['exit']==0

def unchanged_sources():
    identities=json.loads((E/'read-v3r3-constraints-r3/review.json').read_text())['source_sha256']
    for rel,digest in identities.items():assert hashlib.sha256((W/'reference'/rel).read_bytes()).hexdigest()==digest,rel

if mode=='synthesis':
    assert json.loads((E/'read-v3r2-setup/execution.json').read_text())['exit']==0;body=bodies[0]
elif mode=='constraints':
    complete('synthesis')
    body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
open_run synth_read_v3r3
source {@@REF@@/constrs_1/hdmi_cdc.tcl}
source {@@REF@@/constrs_1/ai_monitor_cdc.tcl}
source {@@REF@@/constrs_1/ai_read_monitor_cdc.tcl}
report_timing -from $ai_read_source_C -to $ai_read_capture_D -max_paths 4 -file {@@OUT@@/read-snapshot-path.rpt}
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/ai_read_path_monitor] -file {@@OUT@@/read-CDC.rpt}
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/ai_path_monitor] -file {@@OUT@@/observer-CDC.rpt}
set f [open {@@OUT@@/binding.txt} w]
puts $f "stable_bus_requirement=$ai_read_requirement source_bits=[llength $ai_read_source] capture_bits=[llength $ai_read_capture] source_period=$ai_read_source_period capture_period=$ai_read_capture_period"
puts $f "source_indices=$ai_read_source_indices"
puts $f "capture_indices=$ai_read_capture_indices"
close $f
report_clocks -file {@@OUT@@/clocks.rpt}
ai_read_dump_endpoints {@@OUT@@/read-snapshot-endpoints.txt} $ai_read_source $ai_read_capture
set ::ai_read_clock_report {@@OUT@@/clock-taps.txt}
source {@@REF@@/constrs_1/ai_read_clock_review.tcl}
close_project
puts "AI_READ_V3_CONSTRAINTS_COMPLETE_REVIEW_REQUIRED"
'''
elif mode=='route':
    complete('constraints')
    assert json.loads((E/'read-v3r3-constraints-r3/review.json').read_text())['route_prerequisite_pass']
    unchanged_sources();body=bodies[2]
elif mode=='reports':
    complete('route');body=bodies[3]
    extra=r'''
set read_obs [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/ai_read_path_monitor/*}]
if {[llength $read_obs]<1000} {error "Missing read observer"}
report_timing -max_paths 30 -to $read_obs -file {@@OUT@@/read-setup.rpt}
report_timing -delay_type min -max_paths 30 -to $read_obs -file {@@OUT@@/read-hold.rpt}
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/ai_read_path_monitor] -file {@@OUT@@/read-CDC.rpt}
set src [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/source_snapshot_reg\[[0-9]+\]$}]
set dst [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/csr_snapshot_reg\[[0-9]+\]$}]
set launch [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
set data [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
set paths [get_timing_paths -from $launch -to $data -max_paths 1]
if {![llength $paths]} {error "Read snapshot path absent"}
set p [lindex $paths 0]
set f [open {@@OUT@@/read-snapshot-routed.txt} w]
puts $f "requirement=[get_property REQUIREMENT $p]|slack=[get_property SLACK $p]|source_bits=[llength $src]|capture_bits=[llength $dst]"
close $f
report_timing -from $launch -to $data -max_paths 4 -file {@@OUT@@/read-snapshot.rpt}
ai_read_dump_endpoints {@@OUT@@/read-snapshot-endpoints.txt} $src $dst
set f [open {@@OUT@@/read-snapshot-indices.txt} w]
foreach {label cells} [list source $src capture $dst] {
 set indices {}
 foreach c $cells {if {![regexp {\[([0-9]+)\]$} $c unused index]} {error "Missing bit index $c"};lappend indices $index}
 puts $f "$label=[lsort -integer -unique $indices]"
}
close $f
set ::ai_read_clock_report {@@OUT@@/clock-taps.txt}
source {@@REF@@/constrs_1/ai_read_clock_review.tcl}
'''
    assert body.count('close_project')==1;body=body.replace('close_project',extra+'\nclose_project')
else:
    assert json.loads((E/'read-v3r4-reports/review.json').read_text())['bit_generation_prerequisite_pass']
    unchanged_sources();body=bodies[4]

body=body.replace('synth_monitor_v2','synth_read_v3r3').replace('impl_ai_monitor_v2','impl_read_v3r4')
body=body.replace('ai-monitor-synth-v2.dcp','ai-read-synth-v3.dcp').replace('ai-monitor-routed.dcp','ai-read-routed.dcp')
endpoint_proc=r'''
proc check_managed_ps {} {
 foreach {actual expected} {
  {@@REF@@/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/synth/ps_ai.v} {@@EVIDENCE@@/managed-PS-observer-r2/ps_ai.v.after}
  {@@REF@@/rtl/ps_ai_wrapper.sv} {@@EVIDENCE@@/managed-PS-observer-r2/ps_ai_wrapper.sv.after}
 } {
  set f [open $actual r];fconfigure $f -translation binary;set a [read $f];close $f
  set f [open $expected r];fconfigure $f -translation binary;set b [read $f];close $f
  if {$a ne $b} {error "Managed passive PS output regenerated/changed: $actual"}
 }
}
proc ai_read_dump_endpoints {output src dst} {
 set launch [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
 set data [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
 set paths [get_timing_paths -from $launch -to $data -nworst 1 -max_paths [llength $data]]
 set f [open $output w]
 foreach p $paths {
  puts $f "[get_property ENDPOINT_PIN $p]|requirement=[get_property REQUIREMENT $p]|slack=[get_property SLACK $p]"
 }
 close $f
 if {[llength $paths]!=[llength $dst]} {error "Read snapshot endpoint timing coverage incomplete [llength $paths]/[llength $dst]"}
}
'''
if mode=='synthesis':
    anchor='launch_runs synth_read_v3r3 -jobs 1'
    assert body.count(anchor)==1
    generate=r'''
check_managed_ps
set f [open {@@EVIDENCE@@/read-v3r2-synthesis/managed-BD-run-script.tcl} r]
set script [read $f];close $f
if {![string match {*add_files *fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd*} $script]} {error "Original PS managed BD absent from generated run"}
set f [open {@@OUT@@/managed-BD-run-script.tcl} w];puts $f $script;close $f
puts "MANAGED_PS_BD_DEPENDENCY_RESTORED"
'''
    body=body.replace(anchor,generate+'\n'+anchor)
body=body.replace('close_project','check_managed_ps\nclose_project')
tcl=('if {[catch {\n'+endpoint_proc+'\ncheck_managed_ps\n'+body+'\n} result]} {puts "AI_READ_STAGE_FAILED $result";puts $::errorInfo;exit 1}\nexit\n').replace('@@EVIDENCE@@',E.as_posix())
driver_bytes=Path(__file__).read_bytes()
stage=stage_name(mode)
try:
    out=m.stage(stage,tcl,ceiling=1800 if mode in ('route','synthesis') else 540,
                run_names=['synth_read_v3r3'] if mode in ('synthesis','constraints') else ['impl_read_v3r4'])
finally:
    if (E/stage).exists():(E/stage/'actual-driver.py').write_bytes(driver_bytes)
xpr=W/'reference/fpai_demo_vivado.xpr'
shutil.copyfile(xpr,out/'fpai_demo_vivado.xpr')
