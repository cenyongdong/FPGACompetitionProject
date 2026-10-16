"""Query routed mailbox enable paths; do not alter constraints or implementation."""
from pathlib import Path
import json
import sys

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
W = R / '.local/hdmi-integration-20261016-r1'
assert json.loads((E / 'system-route-r5-reports/execution.json').read_text())['exit'] == 0
sys.path.insert(0, str(W))
import integration_support as s

tcl = r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 open_run impl_hdmi_r5
 set payload [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]}]
 set regs [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set launch [get_pins -of_objects $payload -filter {REF_PIN_NAME == C}]
 set enable [get_pins -of_objects $regs -filter {REF_PIN_NAME == CE}]
 if {![llength $launch] || ![llength $enable]} {error "Mailbox CE query endpoints absent"}
 set paths [get_timing_paths -from $launch -to $enable -max_paths 1000 -nworst 1]
 set f [open {@@OUT@@/CE-paths.txt} w]
 set invalid 0
 foreach path $paths {
  set req [get_property REQUIREMENT $path]
  set slack [get_property SLACK $path]
  puts $f "[get_property STARTPOINT_PIN $path]|[get_property ENDPOINT_PIN $path]|requirement=$req|slack=$slack"
  if {abs($req-5.000)>0.001 || $slack<0} {incr invalid}
 }
 close $f
 report_timing -from $launch -to $enable -max_paths 1000 -nworst 1 -file {@@OUT@@/mailbox-enable.rpt}
 puts "HDMI_ROUTED_MAILBOX_ENABLE_PATHS [llength $paths] INVALID $invalid"
 if {[llength $paths]!=96 || $invalid} {error "Mailbox CE bound coverage or slack failed"}
 close_project
 puts "HDMI_MAILBOX_CE_R5_VERIFIED_NO_CONSTRAINT_MUTATION"
} result]} {puts "HDMI_MAILBOX_CE_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('mailbox-enable-r5', tcl, ceiling=360, run_names=['impl_hdmi_r5'])
