
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 if {![llength [get_files -quiet {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]]} {add_files -fileset constrs_1 -norecurse {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}}
 set xdc [get_files {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]
 set_property USED_IN_SYNTHESIS false $xdc
 set_property PROCESSING_ORDER LATE $xdc
 open_run synth_1
 source {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}
 report_exceptions -coverage -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r2/exceptions-coverage.rpt}
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r2/CDC.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r2/DRC.rpt}
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r2/timing-summary.rpt}
 write_checkpoint -force {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r2/hdmi-constrained-synth.dcp}
 close_project
 puts "HDMI_CDC_CONSTRAINT_BINDING_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_CONSTRAINT_BIND_FAILED $result";puts $::errorInfo;exit 1}
exit
