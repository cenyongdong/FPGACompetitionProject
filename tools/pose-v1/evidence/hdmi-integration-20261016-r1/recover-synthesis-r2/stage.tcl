
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set sr [get_runs synth_1]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/run-state.txt} w]
 puts $f "STATUS|[get_property STATUS $sr]"
 puts $f "NEEDS_REFRESH|[get_property NEEDS_REFRESH $sr]"
 close $f
 if {![string match {*Complete*} [get_property STATUS $sr]]} {error "Recovered synthesis no longer Complete"}
 if {[get_property NEEDS_REFRESH $sr]} {error "Recovered synthesis needs refresh; do not silently reuse"}
 open_run synth_1
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/utilization.rpt}
 report_clocks -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/clocks.rpt}
 set cells [get_cells -hier -filter {NAME =~ *hdmi_display*}]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/HDMI-cells.txt} w]
 foreach c $cells {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/HDMI-registers-and-clocks.txt} w]
 foreach c $cells {if {[string match FD* [get_property REF_NAME $c]]} {puts $f "$c|[get_property REF_NAME $c]|[get_clocks -quiet -of_objects [get_pins -quiet $c/C]]"}}
 close $f
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/recover-synthesis-r2/global-MMCM.txt} w]
 foreach c [get_cells -hier -filter {REF_NAME == MMCME2_ADV}] {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 close_project
 puts "HDMI_R2_SYNTH_METADATA_RECOVERED_NO_RESYNTHESIS"
} result]} {puts "HDMI_RECOVERY_FAILED $result";puts $::errorInfo;exit 1}
exit
