"""Read original factory procedures that contain a clock-route exception."""
import vivado2018_support as s
R=s.R;s.E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';s.W=R/'.local/hdmi-jfm-build-20261016-r1'
src=s.W/'reference/ip_patch/all_src_files.tcl'
tcl=r'''
if {[catch {
 package require md5
 set f [open {@@OUT@@/factory-clock-route-procedures.txt} w]
 source {SOURCE}
 foreach n [lsort [info procs]] {
  if {[string first CLOCK_DEDICATED_ROUTE [info body $n]]>=0} {puts $f "PROCEDURE $n";puts $f [info body $n]}
 }
 close $f
 puts "FACTORY_CLOCK_ROUTE_DEFINITIONS_READ_NO_PATCH_EXECUTED"
} result]} {puts "CLOCK_REVIEW_FAILED $result";exit 1}
exit
'''.replace('SOURCE',src.as_posix())
s.stage('MIG-clock-review',tcl,budget=180,env_extra={'JFM_PATH':str(src.parent.parent)})
