
package require md5
set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/vendor-procedures/procedures.txt} w]
rename open audit_orig_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode ne "r" && $mode ne "rb"} {error "READ_ONLY_OPEN $path $mode"}
 return [eval [linsert $args 0 audit_orig_open $path]]
}
rename file audit_orig_file
proc file {sub args} {
 if {[lsearch -exact {copy delete rename mkdir attributes mtime atime link} $sub]>=0} {error "READ_ONLY_FILE $sub $args"}
 return [eval [linsert $args 0 audit_orig_file $sub]]
}
foreach cmd {exec load create_project open_project set_property set_param} {
 if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "READ_ONLY_COMMAND"}}
}
if {[catch {
 source {D:/FPGACompetitionProject/.local/hdmi-vivado2018-20261016-r2/kit/ip_patch/all_src_files.tcl}
 foreach name {get_vvd_path check_current_platform reset_database_to_default replace_7z030ai_file} {
  puts $f "PROCEDURE $name"
  if {[llength [info procs $name]]} {puts $f [info body $name]}
 }
 puts "PROCEDURE_METADATA_COMPLETE"
} result]} {puts $f "FAILED $result";close $f;exit 1}
close $f
exit
