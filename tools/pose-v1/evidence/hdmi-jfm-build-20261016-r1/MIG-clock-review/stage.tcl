
if {[catch {
 package require md5
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/MIG-clock-review/factory-clock-route-procedures.txt} w]
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/ip_patch/all_src_files.tcl}
 foreach n [lsort [info procs]] {
  if {[string first CLOCK_DEDICATED_ROUTE [info body $n]]>=0} {puts $f "PROCEDURE $n";puts $f [info body $n]}
 }
 close $f
 puts "FACTORY_CLOCK_ROUTE_DEFINITIONS_READ_NO_PATCH_EXECUTED"
} result]} {puts "CLOCK_REVIEW_FAILED $result";exit 1}
exit
