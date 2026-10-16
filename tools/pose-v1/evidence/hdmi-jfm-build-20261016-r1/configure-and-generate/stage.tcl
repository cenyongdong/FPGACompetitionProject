
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set_property ip_repo_paths [list {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/PS_AI IP}] [current_project]
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
 source {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/ip_patch/all_src_files.tcl}
 foreach n {implementation_place_pre.tcl implementation_place_post.tcl} {
  set f [get_files -quiet *$n];if {[llength $f]} {remove_files $f}
 }
 add_hook_tcl_to_prj -xfft_modify FALSE -change_speed FALSE -disable_icap TRUE -device 0
 report_ip_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/configure-and-generate/IP-status.rpt}
 generate_target all [get_ips -all]
 puts "FACTORY_ALL_IP_TARGETS_GENERATED"
 close_project
} result]} {puts "FACTORY_CONFIGURATION_FAILED $result";puts $::errorInfo;exit 1}
exit
