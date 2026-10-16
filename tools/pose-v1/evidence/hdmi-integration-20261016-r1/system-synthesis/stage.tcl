
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/IP-prerequisites.txt} w]
 foreach r [get_runs *_synth_1] {puts $f "$r|[get_property STATUS $r]|[get_property NEEDS_REFRESH $r]"}
 close $f
 reset_run synth_1
 current_run -synthesis [get_runs synth_1]
 launch_runs synth_1 -jobs 1
 wait_on_run synth_1
 set status [get_property STATUS [get_runs synth_1]]
 puts "HDMI_TOP_SYNTHESIS_STATUS $status"
 if {![string match {*Complete*} $status]} {error "HDMI top synthesis did not complete"}
 open_run synth_1
 write_checkpoint -force {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/hdmi-system-synth.dcp}
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/utilization.rpt}
 report_clocks -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/clocks.rpt}
 set cells [get_cells -hier -filter {NAME =~ *hdmi_display*}]
 if {[llength $cells]<100} {error "HDMI integrated cells missing"}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/HDMI-cells.txt} w]
 foreach c $cells {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-synthesis/HDMI-registers-and-clocks.txt} w]
 foreach c $cells {
  set ref [get_property REF_NAME $c]
  if {[string match FD* $ref]} {
   puts $f "$c|$ref|[get_clocks -quiet -of_objects [get_pins -quiet $c/C]]"
  }
 }
 close $f
 close_project
 puts "HDMI_SYSTEM_SYNTHESIS_COMPLETED_NOT_BOARD_ACCEPTANCE"
} result]} {puts "HDMI_SYNTHESIS_FAILED $result";puts $::errorInfo;exit 1}
exit
