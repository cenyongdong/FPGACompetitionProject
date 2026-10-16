
set audit_out {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-pin-review-20261015-r2}
set audit_source {D:/FPGACompetitionProject/.local/hdmi-jfm-pin-review-20261015-r2/kit/ip_patch/all_src_files.tcl}
package require md5
# Create output channels before write guards; use only these channels below.
set audit_result [open [file join $audit_out procedure-inspection.txt] w]
set audit_body [open [file join $audit_out replace_7z030ai_file.body.tcl] w]
set audit_calls [open [file join $audit_out blocked-mutations.txt] w]
set audit_procs [open [file join $audit_out dependency-procedures.tcl] w]
rename open audit_original_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode!="r" && $mode!="rb"} {error "READ_ONLY_GUARD open $path $mode"}
 return [eval [linsert $args 0 audit_original_open $path]]
}
rename file audit_original_file
proc file {subcmd args} {
 if {[lsearch -exact {copy delete rename mkdir attributes mtime atime link} $subcmd]>=0} {
  error "READ_ONLY_GUARD file $subcmd $args"
 }
 return [eval [linsert $args 0 audit_original_file $subcmd]]
}
proc audit_deny {name args} {
 puts $::audit_calls [list $name $args]
 flush $::audit_calls
 error "READ_ONLY_GUARD command $name"
}
foreach name {exec load cd set_property set_param create_project open_project save_project save_project_as
 add_files read_ip upgrade_ip upgrade_bd_cells generate_target launch_runs launch_run synth_design
 write_edif write_bitstream write_checkpoint reset_project close_project} {
 if {[llength [info commands $name]]} {
  rename $name audit_original_$name
  interp alias {} $name {} audit_deny $name
 }
}
set status [catch {source $audit_source} result]
puts $audit_result "SOURCE_STATUS $status"
puts $audit_result "SOURCE_RESULT $result"
if {$status} {puts $audit_result "SOURCE_ERRORINFO $::errorInfo"}
puts $audit_result "REPLACE_COMMANDS [info commands *replace*]"
puts $audit_result "HOOK_COMMANDS [info commands *hook*]"
if {[llength [info procs replace_7z030ai_file]]==1} {
 puts $audit_body [info body replace_7z030ai_file]
 puts $audit_result "REPLACE_ARGUMENTS [info args replace_7z030ai_file]"
 puts $audit_result "REPLACE_BODY_READ 1"
} else {puts $audit_result "REPLACE_BODY_READ 0"}
foreach name [lsort [info procs]] {
 if {[regexp {replace|database|backup|unisim|030|fmsh|migrate|migration|get_vivado|check_version} $name]} {
  puts $audit_procs [list proc $name [info args $name] [info body $name]]
 }
}
close $audit_procs
close $audit_result
close $audit_body
close $audit_calls
puts "JFM_PROCEDURE_INSPECTION_FINISHED source_status=$status"
exit
