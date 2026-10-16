
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_property ip_repo_paths [list {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 report_ip_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/project-status/IP-status.rpt}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/project-status/IP-properties.txt} w]
 foreach ip [get_ips -all] {
  puts $f "IP $ip"
  foreach p {IPDEF IS_LOCKED IP_FILE GENERATE_SYNTH_CHECKPOINT CORE_REVISION} {
   if {[lsearch -exact [list_property $ip] $p]>=0} {puts $f "$p|[get_property $p $ip]"}
  }
 }
 close $f
 puts "ORIGINAL_2018_IP_COUNT [llength [get_ips -all]]"
 puts "ORIGINAL_2018_IP_LOCKED [get_ips -all -filter {IS_LOCKED == 1}]"
 close_project
 puts "ORIGINAL_PROJECT_STATUS_COMPLETE"
} result]} {puts "ORIGINAL_PROJECT_STATUS_FAILED $result";exit 1}
exit
