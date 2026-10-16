"""Constrain future factory hooks to project writes and four authorized GT rules."""
from pathlib import Path
import jfm_build_support as s
import hashlib,shutil
ref=s.W/'reference';run=ref/'ip_patch/run.tcl';before=s.E/'run-tcl-before-guard.tcl'
assert not before.exists();shutil.copyfile(run,before)
guard=r'''
if {![info exists ::jfm_project_guard_installed]} {
 set ::jfm_project_guard_installed 1
 set_param general.maxThreads 2
 package require md5
 rename file jfm_original_file
 proc jfm_install_path p {
  set p [string tolower [jfm_original_file normalize $p]]
  foreach r {d:/vivado18.3 d:/xilinx c:/fudanmicro/procise c:/icraft} {
   if {$p eq $r || [string first "$r/" $p]==0} {return 1}
  }
  return 0
 }
 proc file {sub args} {
  if {$sub in {copy rename}} {
   set dst [lindex $args end]
   if {[jfm_install_path $dst]} {
    set src [lindex $args end-1]
    if {$sub eq "copy" && [jfm_original_file exists $src] && [jfm_original_file exists $dst] && ![jfm_original_file isdirectory $src] && ![jfm_original_file isdirectory $dst] && [md5::md5 -hex -file $src] eq [md5::md5 -hex -file $dst]} {
     puts "JFM_GUARD_SKIP_IDENTICAL_INSTALL_COPY $dst";return
    }
    error "JFM_GUARD_UNPLANNED_INSTALL_WRITE $sub $args"
   }
  } elseif {$sub in {delete mkdir attributes mtime atime link}} {
   foreach p $args {if {[string index $p 0] ne "-" && [jfm_install_path $p]} {error "JFM_GUARD_INSTALL_MUTATION $sub $args"}}
  }
  return [eval [linsert $args 0 jfm_original_file $sub]]
 }
 rename open jfm_original_open
 proc open {p args} {
  if {[llength $args] && [lindex $args 0] ni {r rb} && [jfm_install_path $p]} {error "JFM_GUARD_INSTALL_OPEN $p $args"}
  return [eval [linsert $args 0 jfm_original_open $p]]
 }
 rename launch_runs jfm_original_launch_runs
 proc launch_runs args {
  set i [lsearch -exact $args -jobs]
  if {$i>=0} {set args [lreplace $args [expr {$i+1}] [expr {$i+1}] 1]} else {lappend args -jobs 1}
  puts "JFM_GUARD_SINGLE_JOB $args"
  return [eval [linsert $args 0 jfm_original_launch_runs]]
 }
 rename set_property jfm_original_set_property
 proc set_property args {
  if {[lindex $args 0] eq "IS_ENABLED" && [string tolower [lindex $args 1]] in {0 false}} {
   foreach o [lindex $args 2] {
    if {![catch {get_property CLASS $o} c] && $c eq "rule_check"} {
     set n [get_property NAME $o]
     if {$n ni {REQP-44 REQP-46 REQP-52 REQP-56}} {error "JFM_GUARD_UNAUTHORIZED_DRC_DISABLE $n"}
     puts "JFM_GUARD_FACTORY_GT_RULE_DISABLE $n"
    }
   }
  }
  return [eval [linsert $args 0 jfm_original_set_property]]
 }
}
'''
p=ref/'ip_patch/project_execution_guard.tcl';p.write_text(guard,encoding='utf-8')
run.write_text('source [file join [file dirname [info script]] project_execution_guard.tcl]\n'+before.read_text(encoding='utf-8-sig'),encoding='utf-8')
shutil.copyfile(p,s.E/'project_execution_guard.tcl');shutil.copyfile(run,s.E/'run-tcl-with-guard.tcl')
s.dump(s.E/'execution-guard-review.json',{'original_run_tcl_SHA':hashlib.sha256(before.read_bytes()).hexdigest(),
 'protected_factory_all_src_unmodified':True,'run_wrapper_only_addition':'project guard before original run.tcl',
 'new_installation_writes_blocked':True,'identical_install_copies_skipped':True,'parallel_jobs_forced':1,
 'DRC_disable_allowlist':['REQP-44','REQP-46','REQP-52','REQP-56']})
print('Future project hook guard installed; protected vendor source unchanged')
