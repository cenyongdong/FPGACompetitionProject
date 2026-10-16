"""Run factory Generate Bitstream chain in the isolated reference, capture signoff.
This is flow qualification of original reference RTL, not the corrected HDMI candidate.
"""
import jfm_build_support as s
import json
assert json.loads((s.E/'factory-mig-ooc/execution.json').read_text())['exit']==0
roots=json.loads((s.E/'generation-owner-list.json').read_text())
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 foreach name [list @@OWNERS@@] {
  puts "CREATE_OWNER_OOC_RUN $name"
  create_ip_run [get_files -all $name]
 }
 set f [open {@@OUT@@/runs-before.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property DIRECTORY $r]"}
 close $f
 launch_runs impl_1 -to_step write_bitstream -jobs 1
 wait_on_run impl_1
 set status [get_property STATUS [get_runs impl_1]]
 puts "FACTORY_SYSTEM_RUN_STATUS $status"
 set f [open {@@OUT@@/runs-after.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property PROGRESS $r]"}
 close $f
 if {![string match {*Complete*} $status]} {error "Factory implementation did not complete"}
 open_run impl_1
 report_timing_summary -report_unconstrained -file {@@OUT@@/timing-summary.rpt}
 report_drc -file {@@OUT@@/DRC.rpt}
 report_methodology -file {@@OUT@@/methodology.rpt}
 report_clock_interaction -file {@@OUT@@/clock-interaction.rpt}
 report_cdc -details -file {@@OUT@@/CDC.rpt}
 report_utilization -file {@@OUT@@/utilization.rpt}
 set f [open {@@OUT@@/GT-and-rule-state.txt} w]
 foreach c [get_cells -hier -filter {REF_NAME =~ GTXE2* || REF_NAME =~ GTHE2*}] {puts $f "GT|$c|[get_property REF_NAME $c]"}
 foreach n {REQP-44 REQP-46 REQP-52 REQP-56} {puts $f "RULE|$n|[get_property IS_ENABLED [get_drc_checks $n]]|[get_property SEVERITY [get_drc_checks $n]]"}
 puts $f "PART|[get_property PART [current_design]]"
 close $f
 close_project
 puts "FACTORY_SYSTEM_CHAIN_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "FACTORY_SYSTEM_FAILED $result";puts $::errorInfo;exit 1}
exit
'''.replace('@@OWNERS@@',' '.join('{'+p+'}' for p in roots))
s.stage('factory-system',tcl)
