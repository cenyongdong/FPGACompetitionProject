"""Read actual JFM parameter helpers and DRC definitions; no hooks executed."""
import vivado2018_support as s
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1';W=R/'.local/hdmi-jfm-route2-20261016-r1';s.E=E;s.W=W
source=R/'.local/hdmi-vivado2018-20261016-r2/kit/ip_patch/all_src_files.tcl'
dcp=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/actual-ps-synth/actual_ps.dcp'
tcl='''
if {[catch {
 open_checkpoint {DCP}
 set f [open {@@OUT@@/DRC-properties.txt} w]
 foreach n {REQP-44 REQP-46 REQP-52 REQP-56} {
  set c [get_drc_checks -quiet $n]
  puts $f "DRC $n"
  foreach p [list_property $c] {puts $f "$p|[get_property $p $c]"}
 }
 close $f
 set f [open {@@OUT@@/parameter-procedures.txt} w]
 package require md5
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
 foreach cmd {exec load create_project open_project set_property set_param upgrade_ip upgrade_bd_cells} {
  if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "READ_ONLY_COMMAND"}}
 }
 source {SOURCE}
 foreach n [lsort [info procs]] {
  if {[regexp {^(get_device_value|get_change_speed_value|get_disable_icap_value|generate_final_bit|disable_icap_for_psoc|pre_patch_check|check_need_patch_subcore|replace_ip_database|time_cfg_check|spd_replace|post_write_bitstream_patch|add_hook_tcl_to_prj)$} $n]} {
   puts $f "PROCEDURE $n"
   foreach arg [info args $n] {
    if {[info default $n $arg value]} {puts $f "DEFAULT $arg=$value"}
   }
   puts $f [info body $n]
  }
 }
 close $f
 close_design
 puts "ROUTE2_READONLY_AUDIT_COMPLETE"
} result]} {puts "ROUTE2_READONLY_AUDIT_FAILED $result";exit 1}
exit
'''.replace('DCP',dcp.as_posix()).replace('SOURCE',source.as_posix())
s.stage('parameters-drc',tcl,budget=180,env_extra={'JFM_PATH':str(source.parent.parent)})
