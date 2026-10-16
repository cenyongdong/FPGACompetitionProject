if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 open_run impl_hdmi_r5
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/timing-summary.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/DRC-reopened-default-profile.rpt}
 report_methodology -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/methodology.rpt}
 report_clock_interaction -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/clock-interaction.rpt}
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/CDC.rpt}
 report_bus_skew -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/bus-skew.rpt}
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/utilization.rpt}
 report_clocks -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/clocks.rpt}
 report_timing -max_paths 50 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/HDMI-setup.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 report_timing -delay_type min -max_paths 50 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/HDMI-hold.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/HDMI-clock-physical.txt} w]
 foreach c [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/* && (REF_NAME =~ *MMCME* || REF_NAME =~ BUF* || REF_NAME =~ OSERDESE*)}] {
  puts $f "$c|[get_property REF_NAME $c]|[get_property LOC $c]|[get_property BEL $c]"
  foreach pin [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == CLK || REF_PIN_NAME == CLKDIV || REF_PIN_NAME == O}] {puts $f "PIN|$pin|[get_clocks -quiet -of_objects $pin]"}
 }
 close $f

 report_route_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/route-status.rpt}
 report_exceptions -coverage -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/exceptions-coverage.rpt}
 report_exceptions -ignored -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/exceptions-ignored.rpt}
 set hdmi_root {U0_ps_ai_peripheral/hdmi_display}
 set hdmi_payload [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]}]
 set hdmi_response [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]}]
 set hdmi_capture [get_cells -hier -regexp {.*hdmi_display/scanout/core/core/mailbox/source_response_reg\[[0-9]+\]}]
 if {![llength $hdmi_payload] || ![llength $hdmi_response] || ![llength $hdmi_capture]} {error "Routed mailbox endpoints missing"}
 set hdmi_memory_clock [get_clocks -of_objects [get_pins -of_objects [lindex $hdmi_response 0] -filter {REF_PIN_NAME == C}]]
 set hdmi_memory_regs [filter [all_registers -clock $hdmi_memory_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/mailbox-routed-bounds.txt} w]
 foreach hdmi_item [list [list command $hdmi_payload $hdmi_memory_regs 5.000] [list response $hdmi_response $hdmi_capture 10.000]] {
  lassign $hdmi_item hdmi_name hdmi_src hdmi_dst hdmi_expected
  set hdmi_launch [get_pins -of_objects $hdmi_src -filter {REF_PIN_NAME == C}]
  set hdmi_data [get_pins -of_objects $hdmi_dst -filter {REF_PIN_NAME == D}]
  set hdmi_paths [get_timing_paths -from $hdmi_launch -to $hdmi_data -max_paths 1]
  if {![llength $hdmi_paths]} {error "Routed mailbox constraint absent $hdmi_name"}
  set hdmi_req [get_property REQUIREMENT [lindex $hdmi_paths 0]]
  puts $f "$hdmi_name|requirement=$hdmi_req|slack=[get_property SLACK [lindex $hdmi_paths 0]]|source_bits=[llength $hdmi_src]|destination_regs=[llength $hdmi_dst]"
  report_timing -from $hdmi_launch -to $hdmi_data -max_paths 50 -file "D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r5-reports/mailbox-$hdmi_name.rpt"
  if {abs($hdmi_req-$hdmi_expected)>0.001} {error "Routed mailbox requirement changed $hdmi_name $hdmi_req"}
 }
 close $f

 close_project

 puts "HDMI_ROUTED_REPORTS_COLLECTED_NO_IMPLEMENTATION_RELAUNCH"
} result]} {puts "HDMI_REPORT_COLLECTION_FAILED $result";puts $::errorInfo;exit 1}
exit
