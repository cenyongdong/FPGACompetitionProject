
package require md5
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/fpai_demo_vivado.xpr}
 set audit_root [file normalize {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference}]
 set audit_harc [file normalize {D:/vivado18.3/Vivado/2018.3/data/parts/xilinx/common/HARC.cfg}]
 set audit_log [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/hook-preview/preview-operations.txt} w]
 set out [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/hook-preview/helper-definitions.txt} w]
 rename file audit_orig_file
 proc audit_inside p {
  set p [string tolower [audit_orig_file normalize $p]]
  set root [string tolower $::audit_root]
  return [expr {$p eq $root || [string first "$root/" $p]==0}]
 }
 proc file {sub args} {
  if {$sub eq "copy" || $sub eq "rename"} {
   set dst [lindex $args end]
   if {![audit_inside $dst]} {
    set src [lindex $args end-1]
    if {$sub eq "copy" && [string equal -nocase [audit_orig_file normalize $dst] $::audit_harc] && [md5::md5 -hex -file $src] eq [md5::md5 -hex -file $dst]} {
     puts $::audit_log [list SKIP_IDENTICAL_HARC $src $dst];flush $::audit_log;return
    }
    error "INSTALLATION_WRITE_BLOCKED $sub $args"
   }
   puts $::audit_log [list FILE $sub $args];flush $::audit_log
  } elseif {[lsearch -exact {delete mkdir attributes mtime atime link} $sub]>=0} {
   foreach p $args {if {[string index $p 0] ne "-" && ![audit_inside $p]} {error "OUTSIDE_PROJECT_FILE $sub $p"}}
  }
  return [eval [linsert $args 0 audit_orig_file $sub]]
 }
 rename open audit_orig_open
 proc open {path args} {
  set mode r
  if {[llength $args]>0} {set mode [lindex $args 0]}
  if {$mode ne "r" && $mode ne "rb" && ![audit_inside $path]} {error "OUTSIDE_PROJECT_OPEN $path $mode"}
  return [eval [linsert $args 0 audit_orig_open $path]]
 }
 rename set_property audit_orig_set_property
 proc set_property args {
  puts $::audit_log [list PROPERTY $args];flush $::audit_log
  if {[regexp -nocase {CONFIG\.|MODELPARAM_VALUE\.|IS_ENABLED} [lindex $args 0]]} {error "IP_OR_DRC_MUTATION_BLOCKED $args"}
  return [eval [linsert $args 0 audit_orig_set_property]]
 }
 foreach cmd {exec load upgrade_ip upgrade_bd_cells generate_target synth_design launch_runs launch_run write_bitstream} {
  if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "PREVIEW_NO_EXECUTION"}}
 }
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-route2-20261016-r1/reference/ip_patch/all_src_files.tcl}
 foreach name {disable_icap get_finally_bit_location get_prj_path} {
  puts $out "PROCEDURE $name"
  puts $out "ARGS [info args $name]"
  puts $out [info body $name]
 }
 close $out
 # Remove only inactive references whose files do not exist; no empty substitutes.
 foreach n {implementation_place_pre.tcl implementation_place_post.tcl} {
  set p [get_files -quiet *$n]
  if {[llength $p]} {puts $audit_log "REMOVE_INACTIVE_MISSING_REFERENCE $p";remove_files $p}
 }
 add_hook_tcl_to_prj -xfft_modify FALSE -change_speed FALSE -disable_icap TRUE -device 0
 save_project
 set f [audit_orig_open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1/hook-preview/registered-hooks.txt} w]
 foreach r {synth_1 impl_1} {
  foreach p [list_property [get_runs $r]] {
   if {[regexp {TCL\.(PRE|POST)$} $p]} {puts $f "$r|$p|[get_property $p [get_runs $r]]"}
  }
 }
 close $f
 close $audit_log
 close_project
 puts "ISOLATED_HOOK_CONFIGURATION_PREVIEW_COMPLETE"
} result]} {puts "ISOLATED_HOOK_PREVIEW_FAILED $result";exit 1}
exit
