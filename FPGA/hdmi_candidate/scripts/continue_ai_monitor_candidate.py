"""Resume the isolated observer candidate; staged gates, no board operations."""
from pathlib import Path
import importlib.util,json,sys,hashlib
R=Path(__file__).resolve().parents[3]
W=R/'.local/hdmi-live-20261017-r1'
E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r2'
OLD=R/'tools/pose-v1/evidence/hdmi-live-20261017-r1'
spec=importlib.util.spec_from_file_location('eda_support',W/'eda_support.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.E=E
mode=sys.argv[1]
assert mode in ['synthesis','constraints','route','reports','bit']
assert (E/'resume-review.json').exists()
if mode=='synthesis':
 assert (E/'observer-reset-sample-fix.json').exists()
 body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
if {[llength [get_runs -quiet synth_monitor_v2]]} {error "Preserve previous synthesis"}
set old [get_runs synth_1]
create_run synth_monitor_v2 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
set nr [get_runs synth_monitor_v2]
foreach p [list_property $old] {
 if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
  set val [get_property $p $old]
  if {$val ne ""} {set_property $p $val $nr}
 }
}
current_run -synthesis $nr
launch_runs synth_monitor_v2 -jobs 1
wait_on_run synth_monitor_v2
if {![string match {*Complete*} [get_property STATUS $nr]]} {error "Observer synthesis failed"}
open_run synth_monitor_v2
write_checkpoint {@@OUT@@/ai-monitor-synth-v2.dcp}
report_utilization -file {@@OUT@@/utilization.rpt}
close_project
puts "AI_MONITOR_V2_SYNTHESIS_COMPLETE_NOT_BOARD_ACCEPTANCE"
'''
elif mode=='constraints':
 assert json.loads((E/'monitor-v2-synthesis/execution.json').read_text())['exit']==0
 body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
open_run synth_monitor_v2
source {@@REF@@/constrs_1/hdmi_cdc.tcl}
source {@@REF@@/constrs_1/ai_monitor_cdc.tcl}
report_timing -from [hdmi_cdc_pins $ai_source C] -to [hdmi_cdc_pins $ai_capture D] -max_paths 2 -file {@@OUT@@/observer-snapshot-path.rpt}
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/ai_path_monitor] -file {@@OUT@@/observer-CDC.rpt}
set f [open {@@OUT@@/binding.txt} w]
puts $f "stable_bus_requirement=$ai_requirement source_bits=[llength $ai_source] capture_bits=[llength $ai_capture]"
close $f
close_project
puts "AI_MONITOR_CONSTRAINT_BINDING_COMPLETE_NOT_ROUTED_ACCEPTANCE"
'''
elif mode=='route':
 assert json.loads((E/'monitor-v2-constraints/execution.json').read_text())['exit']==0
 assert json.loads((E/'monitor-v2-constraints/review.json').read_text())['route_prerequisite_pass']
 for rel,expected in json.loads((E/'monitor-v2-constraints/review.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((W/'reference'/rel).read_bytes()).hexdigest()==expected,rel
 body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
set sr [get_runs synth_monitor_v2]
if {![string match {*Complete*} [get_property STATUS $sr]] || [get_property NEEDS_REFRESH $sr]} {error "Synthesis incomplete or stale"}
if {[llength [get_runs -quiet impl_ai_monitor_v2]]} {error "Preserve existing implementation"}
set old [get_runs impl_1]
create_run impl_ai_monitor_v2 -parent_run synth_monitor_v2 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
set nr [get_runs impl_ai_monitor_v2]
set f [open {@@OUT@@/implementation-profile.txt} w]
foreach p {FLOW STRATEGY CONSTRSET PART} {puts $f "$p|[get_property $p $old]|[get_property $p $nr]"}
foreach p [list_property $old] {
 if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
  set val [get_property $p $old]
  if {$val ne ""} {set_property $p $val $nr;puts $f "$p|$val"}
 }
}
set_property STEPS.OPT_DESIGN.TCL.PRE {@@REF@@/ip_patch/process_control/implementation_opt_pre_hdmi.tcl} $nr
puts $f "OBSERVER_AND_HDMI_HOOK|[get_property STEPS.OPT_DESIGN.TCL.PRE $nr]"
close $f
current_run -implementation $nr
launch_runs impl_ai_monitor_v2 -to_step route_design -jobs 1
wait_on_run impl_ai_monitor_v2
set status [get_property STATUS $nr]
puts "AI_MONITOR_ROUTE_STATUS $status"
if {![string match {*route_design Complete*} $status]} {error "Observer implementation failed"}
close_project
puts "AI_MONITOR_ROUTED_NOT_REVIEWED_NO_BITSTREAM"
'''
elif mode=='reports':
 assert json.loads((E/'monitor-v2-route/execution.json').read_text())['exit']==0
 body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
open_run impl_ai_monitor_v2
report_timing_summary -report_unconstrained -file {@@OUT@@/timing-summary.rpt}
report_drc -file {@@OUT@@/DRC-reopened-default-profile.rpt}
report_methodology -file {@@OUT@@/methodology.rpt}
report_clock_interaction -file {@@OUT@@/clock-interaction.rpt}
report_cdc -details -file {@@OUT@@/CDC.rpt}
report_bus_skew -file {@@OUT@@/bus-skew.rpt}
report_utilization -file {@@OUT@@/utilization.rpt}
report_clocks -file {@@OUT@@/clocks.rpt}
report_route_status -file {@@OUT@@/route-status.rpt}
report_exceptions -ignored -file {@@OUT@@/exceptions-ignored.rpt}
set obs [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/ai_path_monitor/*}]
set hdmi [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
if {[llength $obs]<500 || [llength $hdmi]<500} {error "Missing observer/HDMI logic"}
report_timing -max_paths 30 -to $obs -file {@@OUT@@/observer-setup.rpt}
report_timing -delay_type min -max_paths 30 -to $obs -file {@@OUT@@/observer-hold.rpt}
report_timing -max_paths 30 -to $hdmi -file {@@OUT@@/HDMI-setup.rpt}
report_timing -delay_type min -max_paths 30 -to $hdmi -file {@@OUT@@/HDMI-hold.rpt}
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/ai_path_monitor] -file {@@OUT@@/observer-CDC.rpt}
set f [open {@@OUT@@/snapshot-routed-bounds.txt} w]
foreach scope {observer command response} {
 if {$scope eq "observer"} {
  set src [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_path_monitor/source_snapshot_reg\[[0-9]+\]$}]
  set dst [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_path_monitor/csr_snapshot_reg\[[0-9]+\]$}]
  set bound 10.000
 } elseif {$scope eq "command"} {
  set src [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]}]
  set clk [get_clocks clk_pll_i]
  set dst [filter [all_registers -clock $clk] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
  set bound 5.000
 } else {
  set src [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]}]
  set dst [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/source_response_reg\[[0-9]+\]}]
  set bound 10.000
 }
 if {![llength $src] || ![llength $dst]} {error "Snapshot endpoints missing $scope"}
 set launch [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
 set data [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
 set paths [get_timing_paths -from $launch -to $data -max_paths 1]
 if {![llength $paths]} {error "Snapshot path absent $scope"}
 set path [lindex $paths 0]
 set req [get_property REQUIREMENT $path]
 puts $f "$scope|requirement=$req|slack=[get_property SLACK $path]|source_bits=[llength $src]|destination_regs=[llength $dst]"
 if {abs($req-$bound)>0.001} {error "Snapshot requirement wrong $scope $req"}
 report_timing -from $launch -to $data -max_paths 4 -file "@@OUT@@/snapshot-$scope.rpt"
 # Payload capture enables must also be timed; inspect every actual CE path.
 set ce [get_pins -quiet -of_objects $dst -filter {REF_PIN_NAME == CE}]
 set out [open "@@OUT@@/snapshot-$scope-CE.txt" w]
 foreach pin $ce {
  foreach p [get_timing_paths -quiet -from $launch -to $pin -max_paths 1] {
   puts $out "$pin|requirement=[get_property REQUIREMENT $p]|slack=[get_property SLACK $p]"
  }
 }
 close $out
}
close $f
set f [open {@@OUT@@/HDMI-clock-physical.txt} w]
foreach c [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/* && (REF_NAME =~ *MMCME* || REF_NAME =~ BUF* || REF_NAME =~ OSERDESE*)}] {
 puts $f "$c|[get_property REF_NAME $c]|[get_property LOC $c]|[get_property BEL $c]"
 foreach pin [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == CLK || REF_PIN_NAME == CLKDIV || REF_PIN_NAME == O}] {puts $f "PIN|$pin|[get_clocks -quiet -of_objects $pin]"}
}
close $f
write_checkpoint {@@OUT@@/ai-monitor-routed.dcp}
close_project
puts "AI_MONITOR_REPORTS_COMPLETE_REVIEW_REQUIRED"
'''
else:
 assert json.loads((E/'monitor-v2-reports/review.json').read_text())['bit_generation_prerequisite_pass']
 for rel,expected in json.loads((E/'monitor-v2-constraints/review.json').read_text())['source_sha256'].items():
  assert hashlib.sha256((W/'reference'/rel).read_bytes()).hexdigest()==expected,rel
 body=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
set nr [get_runs impl_ai_monitor_v2]
if {![string match {*route_design Complete*} [get_property STATUS $nr]] || [get_property NEEDS_REFRESH $nr]} {error "Reviewed route missing or stale"}
if {[file exists {@@REF@@/fpai_demo_vivado.runs/impl_ai_monitor_v2/ai7030_edif_top.bit}]} {error "Existing bit must be preserved"}
current_run -implementation $nr
launch_runs impl_ai_monitor_v2 -to_step write_bitstream -jobs 1
wait_on_run impl_ai_monitor_v2
if {![string match {*write_bitstream Complete*} [get_property STATUS $nr]]} {error "Bitstream failed"}
close_project
puts "AI_MONITOR_RAW_BIT_COMPLETE_NO_BOARD_OPERATION"
'''
tcl='if {[catch {\n'+body+'\n} result]} {puts "AI_MONITOR_STAGE_FAILED $result";puts $::errorInfo;exit 1}\nexit\n'
m.stage('monitor-v2-'+mode,tcl,ceiling=1800 if mode in ['route','synthesis'] else 540,
        run_names=['synth_monitor_v2'] if mode in ['synthesis','constraints'] else ['impl_ai_monitor_v2'])
