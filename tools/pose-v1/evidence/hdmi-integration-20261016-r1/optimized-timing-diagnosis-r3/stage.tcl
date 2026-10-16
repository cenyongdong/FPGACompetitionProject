
if {[catch {
 set_param general.maxThreads 2
 open_checkpoint {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-input-r3/ai7030_edif_top_opt.dcp}
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/timing-summary.rpt}
 report_timing -max_paths 30 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/global-setup.rpt}
 report_timing -delay_type min -max_paths 20 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/global-hold.rpt}
 set hdmi [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 report_timing -to $hdmi -max_paths 30 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/HDMI-setup.rpt}
 report_timing -to $hdmi -delay_type min -max_paths 20 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/HDMI-hold.rpt}
 report_exceptions -ignored -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/exceptions-ignored.rpt}
 report_clocks -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/optimized-timing-diagnosis-r3/clocks.rpt}
 close_design
 puts "HDMI_OPTIMIZED_TIMING_DIAGNOSIS_COMPLETE_NOT_ROUTED_ACCEPTANCE"
} result]} {puts "HDMI_TIMING_DIAGNOSIS_FAILED $result";puts $::errorInfo;exit 1}
exit
