
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set sr [get_runs synth_1]
 if {![string match {*Complete*} [get_property STATUS $sr]]} {error "Synthesis not complete"}
 if {[get_property NEEDS_REFRESH $sr]} {error "Synthesis needs refresh"}
 if {[llength [get_runs -quiet impl_hdmi_r2]]} {error "Fresh run already exists"}
 set old [get_runs impl_1]
 create_run impl_hdmi_r2 -parent_run synth_1 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
 set nr [get_runs impl_hdmi_r2]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/implementation-profile.txt} w]
 foreach p {FLOW STRATEGY CONSTRSET PART} {puts $f "$p|[get_property $p $old]|[get_property $p $nr]"}
 foreach p [list_property $old] {
  if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
   set val [get_property $p $old]
   if {$val ne ""} {set_property $p $val $nr;puts $f "$p|$val"}
  }
 }
 close $f
 current_run -implementation $nr
 launch_runs impl_hdmi_r2 -to_step route_design -jobs 1
 wait_on_run impl_hdmi_r2
 set status [get_property STATUS $nr]
 puts "HDMI_ROUTED_STATUS $status"
 if {![string match {*route_design Complete*} $status]} {error "Route did not complete"}
 open_run impl_hdmi_r2
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/timing-summary.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/DRC-reopened-default-profile.rpt}
 report_methodology -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/methodology.rpt}
 report_clock_interaction -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/clock-interaction.rpt}
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/CDC.rpt}
 report_bus_skew -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/bus-skew.rpt}
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/utilization.rpt}
 report_clocks -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/clocks.rpt}
 report_timing -max_paths 50 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/HDMI-setup.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 report_timing -delay_type min -max_paths 50 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/HDMI-hold.rpt} -to [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-route-r2/HDMI-clock-physical.txt} w]
 foreach c [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/* && (REF_NAME =~ *MMCME* || REF_NAME =~ BUF* || REF_NAME =~ OSERDESE*)}] {
  puts $f "$c|[get_property REF_NAME $c]|[get_property LOC $c]|[get_property BEL $c]"
  foreach pin [get_pins -quiet -of_objects $c -filter {REF_PIN_NAME == CLK || REF_PIN_NAME == CLKDIV || REF_PIN_NAME == O}] {puts $f "PIN|$pin|[get_clocks -quiet -of_objects $pin]"}
 }
 close $f
 close_project
 puts "HDMI_ROUTE_COMPLETE_NO_BITSTREAM_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_ROUTE_FAILED $result";puts $::errorInfo;exit 1}
exit
