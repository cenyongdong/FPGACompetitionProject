"""Configure a reversible isolated hook preview; never launch runs or patch bits.
Additional installation writes are blocked, including all IP library replacements.
"""
import vivado2018_support as s
from pathlib import Path
import json,shutil
R=s.R;E=R/'tools/pose-v1/evidence/hdmi-jfm-route2-20261016-r1';W=R/'.local/hdmi-jfm-route2-20261016-r1';s.E=E;s.W=W
ref=W/'reference';kit=R/'Docs/26嵌赛开发/JFM_Kits/JFM_Kits/ip_patch';local=ref/'ip_patch';local.mkdir(exist_ok=False)
for n in ['all_src_files.tcl','run.tcl','top.tcl','ip_patch.cfg','ip_patch_version.log','time_check.txt']:
 if (kit/n).exists():shutil.copyfile(kit/n,local/n)
for n in ['process_control','edif','edif_transform','xadc_filter']:
 shutil.copytree(kit/n,local/n)
for n in ['bitfile_replace.tcl','mig_auto_winCheck.tcl']:
 p=local/'tools'/n;p.parent.mkdir(exist_ok=True);shutil.copyfile(kit/'tools'/n,p)
p=local/'device_database/fmk230t/xilinx/HARC.cfg';p.parent.mkdir(parents=True);shutil.copyfile(kit/'device_database/fmk230t/xilinx/HARC.cfg',p)
assert s.sha(local/'all_src_files.tcl')==s.sha(kit/'all_src_files.tcl')
original_bds={p.relative_to(ref).as_posix():s.sha(p) for p in ref.rglob('*') if p.suffix.lower() in ('.xci','.bd')}
s.dump(E/'before-preview-IP-identities.json',original_bds)
tcl=r'''
package require md5
if {[catch {
 open_project {REFROOT/fpai_demo_vivado.xpr}
 set audit_root [file normalize {REFROOT}]
 set audit_harc [file normalize {@@HARC@@}]
 set audit_log [open {@@OUT@@/preview-operations.txt} w]
 set out [open {@@OUT@@/helper-definitions.txt} w]
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
 source {REFROOT/ip_patch/all_src_files.tcl}
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
 set f [audit_orig_open {@@OUT@@/registered-hooks.txt} w]
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
'''.replace('REFROOT',ref.as_posix()).replace('@@HARC@@', 'D:/vivado18.3/Vivado/2018.3/data/parts/xilinx/common/HARC.cfg')
s.stage('hook-preview',tcl,budget=180,env_extra={'JFM_PATH':str(ref),'FMSH_PROCISE_PATH':'C:/FudanMicro/Procise'})
for n,h in original_bds.items():assert s.sha(ref/n)==h,n
generated={p.name:s.sha(p) for p in (local/'process_control').glob('*.tcl')}
s.dump(E/'hook-preview-review.json',{'profile':'review only: xfft_modify FALSE, change_speed FALSE, disable_icap TRUE, device 0',
 'IP_XCI_BD_files_unchanged':len(original_bds),'generated_hook_files':generated,
 'HARC_copy_skipped_as_identical':True,'runs_launched':False,'global_IP_libraries_modified':False,
 'DRC_disables_generated_as_future_script_text_not_executed':True,'full_profile_not_accepted_as_build_baseline':True})
