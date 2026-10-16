"""Read existing hook definitions after import failure; never execute hooks."""
import vivado2018_support as s
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2';W=R/'.local/hdmi-vivado2018-20261016-r2';s.E=E;s.W=W
local=W/'kit/ip_patch'
tcl='''
package require md5
set f [open {@@OUT@@/hook-definitions.txt} w]
rename open audit_orig_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode ne "r" && $mode ne "rb"} {error "READ_ONLY_OPEN"}
 return [eval [linsert $args 0 audit_orig_open $path]]
}
rename file audit_orig_file
proc file {sub args} {
 if {[lsearch -exact {copy delete rename mkdir attributes mtime atime link} $sub]>=0} {error "READ_ONLY_FILE"}
 return [eval [linsert $args 0 audit_orig_file $sub]]
}
foreach cmd {exec load create_project open_project set_property set_param} {
 if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "READ_ONLY_COMMAND"}}
}
if {[catch {
 source {SOURCE}
 foreach name [lsort [info procs]] {
  if {[regexp -nocase {hook|edif|synthesis_patch|opt_design_patch|write_bitstream_patch|runEco|procise} $name]} {
   puts $f "PROCEDURE $name"
   puts $f "ARGS [info args $name]"
   puts $f [info body $name]
  }
 }
 puts "READ_ONLY_JFM_FLOW_COMPLETE"
} result]} {puts $f "FAIL $result";close $f;exit 1}
close $f
exit
'''.replace('SOURCE',(local/'all_src_files.tcl').as_posix())
s.stage('flow-reading',tcl,budget=180,env_extra={'JFM_PATH':str(local.parent)})
