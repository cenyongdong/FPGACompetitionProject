"""Collect the completed r5 route's reports separately; never rerun a run."""
from pathlib import Path
import sys, json

R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-integration-20261016-r1'
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
assert json.loads((E / 'system-route-r5/execution.json').read_text())['exit'] == 0
script = (E / 'system-route-r5/stage.tcl').read_text(encoding='utf-8')
body = script[script.index(' open_run impl_hdmi_r5'):script.index(' puts "HDMI_ROUTE_COMPLETE_NO_BITSTREAM_REPORTS_REQUIRE_REVIEW"')]
old_out = (E / 'system-route-r5').as_posix()
body = body.replace(old_out, '@@OUT@@')
extra = r'''
 report_route_status -file {@@OUT@@/route-status.rpt}
 report_exceptions -coverage -file {@@OUT@@/exceptions-coverage.rpt}
 report_exceptions -ignored -file {@@OUT@@/exceptions-ignored.rpt}
 set hdmi_root {U0_ps_ai_peripheral/hdmi_display}
 set hdmi_payload [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]}]
 set hdmi_response [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]}]
 set hdmi_capture [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/source_response_reg\[[0-9]+\]}]
 if {![llength $hdmi_payload] || ![llength $hdmi_response] || ![llength $hdmi_capture]} {error "Routed mailbox endpoints missing"}
 set hdmi_memory_clock [get_clocks -of_objects [get_pins -of_objects [lindex $hdmi_response 0] -filter {REF_PIN_NAME == C}]]
 set hdmi_memory_regs [filter [all_registers -clock $hdmi_memory_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {@@OUT@@/mailbox-routed-bounds.txt} w]
 foreach hdmi_item [list [list command $hdmi_payload $hdmi_memory_regs 5.000] [list response $hdmi_response $hdmi_capture 10.000]] {
  lassign $hdmi_item hdmi_name hdmi_src hdmi_dst hdmi_expected
  set hdmi_launch [get_pins -of_objects $hdmi_src -filter {REF_PIN_NAME == C}]
  set hdmi_data [get_pins -of_objects $hdmi_dst -filter {REF_PIN_NAME == D}]
  set hdmi_paths [get_timing_paths -from $hdmi_launch -to $hdmi_data -max_paths 1]
  if {![llength $hdmi_paths]} {error "Routed mailbox constraint absent $hdmi_name"}
  set hdmi_req [get_property REQUIREMENT [lindex $hdmi_paths 0]]
  puts $f "$hdmi_name|requirement=$hdmi_req|slack=[get_property SLACK [lindex $hdmi_paths 0]]|source_bits=[llength $hdmi_src]|destination_regs=[llength $hdmi_dst]"
  report_timing -from $hdmi_launch -to $hdmi_data -max_paths 50 -file "@@OUT@@/mailbox-$hdmi_name.rpt"
  if {abs($hdmi_req-$hdmi_expected)>0.001} {error "Routed mailbox requirement changed $hdmi_name $hdmi_req"}
 }
 close $f
'''
assert body.count('\n close_project\n') == 1
body = body.replace('\n close_project\n', '\n' + extra + '\n close_project\n')
tcl = ('if {[catch {\n open_project {@@REF@@/fpai_demo_vivado.xpr}\n set_param general.maxThreads 2\n' + body +
       '\n puts "HDMI_ROUTED_REPORTS_COLLECTED_NO_IMPLEMENTATION_RELAUNCH"\n' +
       '} result]} {puts "HDMI_REPORT_COLLECTION_FAILED $result";puts $::errorInfo;exit 1}\nexit\n')
assert 'launch_runs' not in tcl and 'reset_run' not in tcl
sys.path.insert(0, str(W))
import integration_support as s
s.stage('system-route-r5-reports', tcl, ceiling=540, run_names=['impl_hdmi_r5'])
