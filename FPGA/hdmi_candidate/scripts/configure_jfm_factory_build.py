"""Original reference qualification, no candidate integration or board operation yet."""
import jfm_build_support as s
from pathlib import Path
import json,hashlib
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
apply=json.loads((s.E/'IP-library-apply.json').read_text())
assert apply['complete'] and len(apply['attempted'])==32
for x in apply['attempted']:assert sha(Path(apply['installation'])/x['relative'])==x['source_SHA']
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set_property ip_repo_paths [list {@@REF@@/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 if {[llength [get_ips -all -filter {IS_LOCKED == 1}]]} {error "Original IP unexpectedly locked"}
 # Guard Tcl-controlled writes to the installation; all future hooks inherit it
 # through their normal source run.tcl. This setup guard remains active here.
 package require md5
 rename file audit_file
 proc file {sub args} {
  if {$sub in {copy rename}} {
   set dst [audit_file normalize [lindex $args end]]
   if {[string first "d:/vivado18.3/" [string tolower $dst]]==0} {
    set src [lindex $args end-1]
    if {$sub eq "copy" && [audit_file exists $dst] && [md5::md5 -hex -file $src] eq [md5::md5 -hex -file $dst]} {puts "SKIP_IDENTICAL_INSTALL_COPY $dst";return}
    error "UNPLANNED_INSTALL_WRITE $dst"
   }
  } elseif {$sub in {delete mkdir attributes mtime atime link}} {
   foreach p $args {
    if {[string index $p 0] ne "-" && [string first "d:/vivado18.3/" [string tolower [audit_file normalize $p]]]==0} {error "UNPLANNED_INSTALL_MUTATION $sub $p"}
   }
  }
  return [eval [linsert $args 0 audit_file $sub]]
 }
 source {@@REF@@/ip_patch/all_src_files.tcl}
 foreach n {implementation_place_pre.tcl implementation_place_post.tcl} {
  set f [get_files -quiet *$n];if {[llength $f]} {remove_files $f}
 }
 add_hook_tcl_to_prj -xfft_modify FALSE -change_speed FALSE -disable_icap TRUE -device 0
 report_ip_status -file {@@OUT@@/IP-status.rpt}
 generate_target all [get_ips -all]
 puts "FACTORY_ALL_IP_TARGETS_GENERATED"
 close_project
} result]} {puts "FACTORY_CONFIGURATION_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('configure-and-generate',tcl)
