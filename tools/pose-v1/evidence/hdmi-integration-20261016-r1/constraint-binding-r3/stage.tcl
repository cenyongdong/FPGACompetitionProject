
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 if {![llength [get_files -quiet {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]]} {add_files -fileset constrs_1 -norecurse {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}}
 set xdc [get_files {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]
 set_property USED_IN_SYNTHESIS false $xdc
 set_property PROCESSING_ORDER LATE $xdc
 open_run synth_1
 source {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}
 report_exceptions -coverage -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/exceptions-coverage.rpt}
 report_exceptions -ignored -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/exceptions-ignored.rpt}
 set command [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
 set response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
 set capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
 set mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $response 0] C]]
 set memory_regs [filter [all_registers -clock $mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/mailbox-bound-check.txt} w]
 foreach item [list [list command $command $memory_regs 5.000] [list response $response $capture 10.000]] {
  lassign $item name src dst expected
  set paths [get_timing_paths -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20]
  if {![llength $paths]} {error "HDMI_MAILBOX_BOUND_IGNORED $name"}
  foreach p $paths {
   set req [get_property REQUIREMENT $p]
   if {abs($req-$expected)>0.001} {error "HDMI_MAILBOX_BOUND_WRONG $name $req"}
   puts $f "$name|requirement=$req|[get_property STARTPOINT_PIN $p]|[get_property ENDPOINT_PIN $p]"
  }
  report_timing -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20 -file "D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/mailbox-$name.rpt"
 }
 close $f
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/CDC.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/DRC.rpt}
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/timing-summary.rpt}
 write_checkpoint -force {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r3/hdmi-constrained-synth.dcp}
 close_project
 puts "HDMI_CDC_CONSTRAINT_BINDING_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_CONSTRAINT_BIND_FAILED $result";puts $::errorInfo;exit 1}
exit
