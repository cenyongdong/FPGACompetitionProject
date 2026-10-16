
if {[catch {
 package require md5
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/build-controls-r2/build-control-procedures.txt} w]
 rename exec audit_exec
 proc exec args {error "READ_ONLY"}
 rename open audit_open
 proc open {p args} {
  if {[llength $args]>0 && [lindex $args 0] ni {r rb}} {error "READ_ONLY_OPEN"}
  return [eval [linsert $args 0 audit_open $p]]
 }
 rename file audit_file
 proc file {sub args} {
  if {$sub in {copy delete rename mkdir attributes mtime atime link}} {error "READ_ONLY_FILE"}
  return [eval [linsert $args 0 audit_file $sub]]
 }
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/ip_patch/all_src_files.tcl}
 foreach n [lsort [info procs]] {
  if {[regexp -nocase {^(runEco.*|pre_synthesis_patch|source_file_backup|.*speed.*|.*database.*|.*synthesis.*patch.*|.*files.*|post_.*patch)$} $n]} {
   puts $f "PROCEDURE $n";puts $f "ARGS [info args $n]";puts $f [info body $n]
  }
 }
 close $f
 puts "READ_ONLY_BUILD_CONTROLS_COMPLETE"
} result]} {puts "READ_ONLY_BUILD_CONTROLS_FAILED $result";exit 1}
exit
