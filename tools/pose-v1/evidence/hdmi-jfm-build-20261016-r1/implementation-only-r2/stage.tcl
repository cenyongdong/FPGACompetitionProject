
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set sr [get_runs synth_1]
 if {![string match {*Complete*} [get_property STATUS $sr]]} {error "Completed synthesis prerequisite missing"}
 if {[get_property NEEDS_REFRESH $sr]} {error "Synthesis identity needs refresh; do not silently reuse"}
 if {[llength [get_runs -quiet impl_r2]]} {error "Fresh implementation run already exists"}
 set old [get_runs impl_1]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/implementation-profile.txt} w]
 foreach p {FLOW STRATEGY CONSTRSET PART} {puts $f "$p|[get_property $p $old]"}
 create_run impl_r2 -parent_run synth_1 -flow [get_property FLOW $old] -strategy [get_property STRATEGY $old] -constrset [get_property CONSTRSET $old]
 set nr [get_runs impl_r2]
 foreach p [list_property $old] {
  if {[regexp {^STEPS\..*\.TCL\.(PRE|POST)$} $p]} {
   set val [get_property $p $old]
   if {$val ne ""} {set_property $p $val $nr;puts $f "$p|$val"}
  }
 }
 close $f
 current_run -implementation $nr
 launch_runs impl_r2 -to_step write_bitstream -jobs 1
 wait_on_run impl_r2
 set status [get_property STATUS $nr]
 puts "FACTORY_IMPL_R2_STATUS $status"
 if {![string match {*Complete*} $status]} {error "New implementation did not complete"}
 open_run impl_r2
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/timing-summary.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/DRC.rpt}
 report_methodology -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/methodology.rpt}
 report_clock_interaction -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/clock-interaction.rpt}
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/CDC.rpt}
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/utilization.rpt}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/implementation-only-r2/GT-and-rule-state.txt} w]
 foreach c [get_cells -hier -filter {REF_NAME =~ GTXE2* || REF_NAME =~ GTHE2*}] {puts $f "GT|$c|[get_property REF_NAME $c]"}
 foreach n {REQP-44 REQP-46 REQP-52 REQP-56} {puts $f "RULE|$n|[get_property IS_ENABLED [get_drc_checks $n]]|[get_property SEVERITY [get_drc_checks $n]]"}
 close $f
 close_project
 puts "FACTORY_IMPLEMENTATION_R2_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "FACTORY_IMPL_R2_FAILED $result";puts $::errorInfo;exit 1}
exit
