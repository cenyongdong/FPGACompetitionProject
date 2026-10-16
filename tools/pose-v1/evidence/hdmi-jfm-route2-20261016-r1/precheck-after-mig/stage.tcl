
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/fpai_demo_vivado.xpr}
 package require md5
 rename exec audit_exec
 proc exec args {error "NO_EXTERNAL_EXEC_ALLOWED"}
 foreach cmd {set_property upgrade_ip upgrade_bd_cells generate_target synth_design launch_runs write_bitstream} {
  if {[llength [info commands $cmd]]} {rename $cmd audit_$cmd;proc $cmd args {error "READ_ONLY_PRECHECK"}}
 }
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/ip_patch/all_src_files.tcl}
 set status [catch {pre_patch_check} result]
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/precheck-after-mig/precheck.txt} w]
 puts $f "PRECHECK_STATUS $status";puts $f "PRECHECK_RESULT $result";close $f
 if {$status} {error $result}
 close_project
 puts "FACTORY_PRECHECK_AFTER_MIG_PASS"
} result]} {puts "FACTORY_PRECHECK_FAILED $result";exit 1}
exit
