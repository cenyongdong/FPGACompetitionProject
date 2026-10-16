"""Route integrated HDMI through the qualified factory flow, without a bitstream.

Requires reviewed pre-implementation constraints. Reuses completed synthesis;
keeps all original hook/strategy settings and writes to a fresh implementation.
"""
from pathlib import Path
import sys, json, hashlib, shutil

R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-integration-20261016-r1'
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
revision = sys.argv[1] if len(sys.argv) > 1 else 'r2'
assert revision in ('r2', 'r3', 'r4')
binding_revision = 'r5' if revision == 'r4' else 'r4'
review = json.loads((E / ('constraint-binding-' + binding_revision) / 'review.json').read_text())
assert review['route_prerequisite_pass']
assert json.loads((E / ('constraint-binding-' + binding_revision) / 'execution.json').read_text())['exit'] == 0
assert json.loads((E / 'sim-phy-r3/result.json').read_text())['passed']
for relative, sha in review['bound_source_sha256'].items():
    assert hashlib.sha256((W / 'reference' / relative).read_bytes()).hexdigest() == sha, relative
sys.path.insert(0, str(W))
import integration_support as s
run_name = 'impl_hdmi_' + revision
if revision in ('r3', 'r4'):
    assert (E / 'system-route-r2/cleanup-inventory-post.json').exists()
    source = R / 'FPGA/hdmi_candidate/constraints/hdmi_cdc.xdc'
    shutil.copyfile(source, W / 'reference/constrs_1/hdmi_cdc.tcl')
    wrapper = W / 'reference/ip_patch/process_control/implementation_opt_pre_hdmi.tcl'
    wrapper.write_text(r'''
source [file join [file dirname [info script]] implementation_opt_pre.tcl]
if {[info exists ::hdmi_cdc_constraints_applied]} {error "HDMI constraints applied before dedicated hook"}
source [file normalize [file join [file dirname [info script]] ../../constrs_1/hdmi_cdc.tcl]]
set hdmi_source [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
set hdmi_response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
set hdmi_capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
set hdmi_mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $hdmi_response 0] C]]
set hdmi_memory_regs [filter [all_registers -clock $hdmi_mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
foreach hdmi_item [list [list command $hdmi_source $hdmi_memory_regs 5.000] [list response $hdmi_response $hdmi_capture 10.000]] {
 lassign $hdmi_item hdmi_name hdmi_src hdmi_dst hdmi_expected
 set hdmi_paths [get_timing_paths -from [hdmi_cdc_pins $hdmi_src C] -to [hdmi_cdc_pins $hdmi_dst D] -max_paths 1]
 if {![llength $hdmi_paths]} {error "HDMI_IMPL_MAILBOX_BOUND_ABSENT $hdmi_name"}
 set hdmi_req [get_property REQUIREMENT [lindex $hdmi_paths 0]]
 if {abs($hdmi_req-$hdmi_expected)>0.001} {error "HDMI_IMPL_MAILBOX_BOUND_WRONG $hdmi_name $hdmi_req"}
 puts "HDMI_IMPL_MAILBOX_BOUND_ACTIVE $hdmi_name $hdmi_req"
}
puts "HDMI_IMPL_PROCEDURAL_CONSTRAINT_HOOK_APPLIED"
''', encoding='utf-8')

tcl = r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 if {"@@REV@@" ne "r2"} {
  set hdmi_xdc [get_files {@@REF@@/constrs_1/hdmi_cdc.xdc}]
  set_property USED_IN_SYNTHESIS false $hdmi_xdc
  set_property USED_IN_IMPLEMENTATION false $hdmi_xdc
 }
 set sr [get_runs synth_1]
 if {![string match {*Complete*} [get_property STATUS $sr]]} {error "Synthesis not complete"}
 if {[get_property NEEDS_REFRESH $sr]} {error "Synthesis needs refresh"}
 if {[llength [get_runs -quiet @@RUN@@]]} {error "Fresh run already exists"}
 set old [get_runs impl_1]
 create_run @@RUN@@ -parent_run synth_1 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
 set nr [get_runs @@RUN@@]
 set f [open {@@OUT@@/implementation-profile.txt} w]
 foreach p {FLOW STRATEGY CONSTRSET PART} {puts $f "$p|[get_property $p $old]|[get_property $p $nr]"}
 foreach p [list_property $old] {
  if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
   set val [get_property $p $old]
   if {$val ne ""} {set_property $p $val $nr;puts $f "$p|$val"}
  }
 }
 if {"@@REV@@" ne "r2"} {
  set_property STEPS.OPT_DESIGN.TCL.PRE {@@REF@@/ip_patch/process_control/implementation_opt_pre_hdmi.tcl} $nr
  puts $f "HDMI_WRAPPER|[get_property STEPS.OPT_DESIGN.TCL.PRE $nr]"
 }
 close $f
 current_run -implementation $nr
 launch_runs @@RUN@@ -to_step route_design -jobs 1
 wait_on_run @@RUN@@
 set status [get_property STATUS $nr]
 puts "HDMI_ROUTED_STATUS $status"
 if {![string match {*route_design Complete*} $status]} {error "Route did not complete"}
 open_run @@RUN@@
 report_timing_summary -report_unconstrained -file {@@OUT@@/timing-summary.rpt}
 report_drc -file {@@OUT@@/DRC-reopened-default-profile.rpt}
 report_methodology -file {@@OUT@@/methodology.rpt}
 report_clock_interaction -file {@@OUT@@/clock-interaction.rpt}
 report_cdc -details -file {@@OUT@@/CDC.rpt}
 report_bus_skew -file {@@OUT@@/bus-skew.rpt}
 report_utilization -file {@@OUT@@/utilization.rpt}
 report_clocks -file {@@OUT@@/clocks.rpt}
 report_timing -max_paths 50 -file {@@OUT@@/HDMI-setup.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 report_timing -delay_type min -max_paths 50 -file {@@OUT@@/HDMI-hold.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {@@OUT@@/HDMI-clock-physical.txt} w]
 foreach c [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/* && (REF_NAME =~ *MMCME* || REF_NAME =~ BUF* || REF_NAME =~ OSERDESE*)}] {
  puts $f "$c|[get_property REF_NAME $c]|[get_property LOC $c]|[get_property BEL $c]"
  foreach pin [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == CLK || REF_PIN_NAME == CLKDIV || REF_PIN_NAME == O}] {puts $f "PIN|$pin|[get_clocks -quiet -of_objects $pin]"}
 }
 close $f
 close_project
 puts "HDMI_ROUTE_COMPLETE_NO_BITSTREAM_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_ROUTE_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
tcl = tcl.replace('@@REV@@', revision).replace('@@RUN@@', run_name)
s.stage('system-route-' + revision, tcl, ceiling=1800, run_names=[run_name])
