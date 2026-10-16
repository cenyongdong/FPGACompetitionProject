
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 add_files -norecurse [glob {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/rtl/hdmi_candidate/*}]
 add_files -fileset constrs_1 -norecurse {D:/FPGACompetitionProject/.local/hdmi-integration-20261016-r1/reference/constrs_1/hdmi_input.xdc}
 set_property TOP ai7030_edif_top [get_filesets sources_1]
 update_compile_order -fileset sources_1
 report_ip_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/configure-and-syntax/IP-status.rpt}
 foreach ip [get_ips -all] {
  if {[get_property IS_LOCKED $ip]} {error "Locked IP encountered: $ip"}
 }
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/configure-and-syntax/source-order.txt} w]
 foreach x [get_files -compile_order sources -used_in synthesis] {puts $f $x}
 close $f
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-integration-20261016-r1/configure-and-syntax/runs.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property NEEDS_REFRESH $r]|[get_property DIRECTORY $r]"}
 close $f
 check_syntax -fileset sources_1
 close_project
 puts "HDMI_SYSTEM_SOURCE_SYNTAX_AND_IP_STATUS_COMPLETED"
} result]} {puts "HDMI_CONFIGURE_FAILED $result";puts $::errorInfo;exit 1}
exit
