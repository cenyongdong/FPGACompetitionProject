
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 if {![llength [get_files -quiet {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]]} {add_files -fileset constrs_1 -norecurse {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}}
 set xdc [get_files {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}]
 set_property USED_IN_SYNTHESIS false $xdc
 set_property PROCESSING_ORDER LATE $xdc
 open_run synth_1
 source {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_cdc.xdc}
 report_exceptions -coverage -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/exceptions-coverage.rpt}
 report_exceptions -ignored -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/exceptions-ignored.rpt}
 set command [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
 set response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
 set capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
 set mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $response 0] C]]
 set memory_regs [filter [all_registers -clock $mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/mailbox-bound-check.txt} w]
 foreach item [list [list command $command $memory_regs 5.000] [list response $response $capture 10.000]] {
  lassign $item name src dst expected
  set paths [get_timing_paths -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20]
  if {![llength $paths]} {error "HDMI_MAILBOX_BOUND_IGNORED $name"}
  foreach p $paths {
   set req [get_property REQUIREMENT $p]
   if {abs($req-$expected)>0.001} {error "HDMI_MAILBOX_BOUND_WRONG $name $req"}
   puts $f "$name|requirement=$req|[get_property STARTPOINT_PIN $p]|[get_property ENDPOINT_PIN $p]"
  }
  report_timing -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20 -file "D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/mailbox-$name.rpt"
 }
 close $f
 if {[llength [info commands hdmi_cdc_cells]] && [string match *r5* {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5}]} {
  set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/FIFO-local-reset-drivers.txt} w]
  set state [get_cells -hier -regexp {^U0_ps_ai_peripheral/hdmi_display/scanout/fifo/(wr_bin|wr_gray|rd_bin|rd_gray|wr_sync1|wr_sync2|rd_sync1|rd_sync2|lane)_reg\[[0-9]+\]$}]
  if {[llength $state]<40} {error "HDMI_FIFO_STATE_MISSING"}
  foreach c $state {
   set clear [hdmi_cdc_pins $c CLR]
   if {[llength $clear]!=1} {error "HDMI_FIFO_RESET_PIN_MISSING $c"}
   set drivers [all_fanin -flat -startpoints_only -only_cells -to $clear]
   if {[llength $drivers]!=1 || ![regexp {/fifo/(wr|rd)_release_reg\[2\]$} $drivers]} {error "HDMI_FIFO_RESET_NOT_LOCAL $c $drivers"}
   set src $drivers
   set src_clock [get_clocks -of_objects [hdmi_cdc_pins $src C]]
   set dst_clock [get_clocks -of_objects [hdmi_cdc_pins $c C]]
   if {$src_clock ne $dst_clock || [llength $src_clock]!=1} {error "HDMI_FIFO_RESET_DOMAIN_MISMATCH $c $drivers $src_clock $dst_clock"}
   puts $f "$c|$drivers|clock=$dst_clock"
  }
  close $f
  puts "HDMI_FIFO_STATE_RESET_LOCAL_CLOCK_PROOF [llength $state]"
 }
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/CDC.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/DRC.rpt}
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/timing-summary.rpt}
 write_checkpoint -force {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/constraint-binding-r5/hdmi-constrained-synth.dcp}
 close_project
 puts "HDMI_CDC_CONSTRAINT_BINDING_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_CONSTRAINT_BIND_FAILED $result";puts $::errorInfo;exit 1}
exit
