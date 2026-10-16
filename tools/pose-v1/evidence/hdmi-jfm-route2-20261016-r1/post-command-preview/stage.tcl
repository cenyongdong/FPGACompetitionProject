
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/fpai_demo_vivado.xpr}
 set audit_root [file normalize {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1}]
 set audit_out [file normalize {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/post-command-preview}]
 set audit_log [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/post-command-preview/post-command-preview.txt} w]
 set prop [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/post-command-preview/registered-hooks-and-IP.txt} w]
 foreach r {synth_1 impl_1} {
  foreach p [list_property [get_runs $r]] {
   if {[regexp {TCL.(PRE|POST)$} $p]} {puts $prop "$r|$p|[get_property $p [get_runs $r]]"}
  }
 }
 foreach ip [get_ips -all] {
  puts $prop "IP|$ip|[get_property IS_LOCKED $ip]"
  set f [get_files -all -quiet [get_property IP_FILE $ip]]
  if {[llength $f]==1} {
   foreach p {GENERATE_SYNTH_CHECKPOINT IS_MANAGED} {
    if {[lsearch -exact [list_property $f] $p]>=0} {puts $prop "FILE_PROPERTY|$ip|$p|[get_property $p $f]"}
   }
  }
 }
 close $prop
 package require md5
 rename open audit_orig_open
 proc audit_inside p {
  set p [string tolower [file normalize $p]]
  foreach r [list $::audit_root $::audit_out] {
   set r [string tolower $r]
   if {$p eq $r || [string first "$r/" $p]==0} {return 1}
  }
  return 0
 }
 proc open {path args} {
  set mode r
  if {[llength $args]>0} {set mode [lindex $args 0]}
  if {$mode ne "r" && $mode ne "rb" && ![audit_inside $path]} {error "OUTSIDE_AUDIT_OPEN $path $mode"}
  return [eval [linsert $args 0 audit_orig_open $path]]
 }
 rename file audit_orig_file
 proc file {sub args} {
  if {$sub eq "copy" || $sub eq "rename"} {
   if {![audit_inside [lindex $args end]]} {error "OUTSIDE_AUDIT_FILE $sub $args"}
  } elseif {$sub eq "delete"} {
   foreach p $args {if {[string index $p 0] ne "-" && ![audit_inside $p]} {error "OUTSIDE_AUDIT_DELETE $p"}}
  }
  return [eval [linsert $args 0 audit_orig_file $sub]]
 }
 rename exec audit_orig_exec
 proc exec args {puts $::audit_log [list SUPPRESSED_EXEC $args];flush $::audit_log;return ""}
 foreach cmd {set_property upgrade_ip upgrade_bd_cells generate_target synth_design launch_runs write_bitstream} {
  if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "READ_ONLY_PROJECT_COMMAND"}}
 }
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/ip_patch/all_src_files.tcl}
 set precheck [catch {pre_patch_check} result]
 puts $audit_log "PRECHECK_STATUS $precheck"
 puts $audit_log "PRECHECK_RESULT $result"
 # Exactly one copied reference .bit in the clean work directory. No new .bit output.
 post_write_bitstream_patch -disable_icap TRUE -device 0 -change_speed FALSE -xfft_modify FALSE
 puts $audit_log "POST_BRANCH_PREVIEW_COMPLETE_NOT_EXECUTED"
 close $audit_log
 close_project
 puts "POST_COMMAND_PREVIEW_COMPLETE_NOT_BIT_PATCHED"
} result]} {puts "POST_COMMAND_PREVIEW_FAILED $result";exit 1}
exit
