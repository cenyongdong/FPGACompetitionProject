
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set nr [get_runs impl_hdmi_r5]
 if {![string match {*route_design Complete*} [get_property STATUS $nr]]} {error "Reviewed routed run missing"}
 if {[get_property NEEDS_REFRESH $nr]} {error "Routed run needs refresh"}
 if {[file exists {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.runs/impl_hdmi_r5/ai7030_edif_top.bit}]} {error "Preserve existing bit; do not overwrite"}
 current_run -implementation $nr
 launch_runs impl_hdmi_r5 -to_step write_bitstream -jobs 1
 wait_on_run impl_hdmi_r5
 set status [get_property STATUS $nr]
 puts "HDMI_WRITE_BITSTREAM_STATUS $status"
 if {![string match {*write_bitstream Complete*} $status]} {error "Bit generation not complete"}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/system-bit-r5/actual-bit-products.txt} w]
 foreach p [glob -nocomplain {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.runs/impl_hdmi_r5/*.bit}] {puts $f "$p|[file size $p]"}
 close $f
 close_project
 puts "HDMI_RAW_BIT_COMPLETE_NOT_BOARD_ACCEPTANCE"
} result]} {puts "HDMI_WRITE_BITSTREAM_FAILED $result";puts $::errorInfo;exit 1}
exit
