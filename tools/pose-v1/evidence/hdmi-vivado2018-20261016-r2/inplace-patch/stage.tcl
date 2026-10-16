
package require md5
set audit_log [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/inplace-patch/mutations.txt} w]
set audit_allowed [list {d:/vivado18.3/vivado/2018.3/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tcsg324_pkg.xml} {d:/vivado18.3/vivado/2018.3/data/ip/xilinx/mig_7series_v4_2/data/fpga_tlib/artix7/7a/xc7a50tfgg484_pkg.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7.rtd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7.xng} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/partstats.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/clockregion.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/csg324/package.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/fgg484/package.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.tile2bfd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t.xng} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/artix7/devint/artix7/xc7a50t/xc7a50t_tiles.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/common/unisim.btl} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/common/unisims} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/sitemap2.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.lib} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.padr} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.rtd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.rtd.bak} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.xng} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/partstats.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/clockregion.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.paspd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.rtd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.tile2bfd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015.xng} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z015/xc7z015_tiles.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z030/xc7z030.paspd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/clockregion.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.rtd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tile2bfd} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.tld} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045.xng} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z045/xc7z045_tiles.xml} {d:/vivado18.3/vivado/2018.3/data/parts/xilinx/zynq/devint/zynq/xc7z100/xc7z100.paspd} {d:/vivado18.3/vivado/2018.3/scripts/rt/data/unisim_comp.lib} {d:/vivado18.3/vivado/2018.3/scripts/rt/data/unisim_comp.v}]
set audit_local {D:/FPGACompetitionProject/.local/hdmi-vivado2018-20261016-r2/kit/ip_patch}
rename file audit_orig_file
proc audit_key p {return [string tolower [audit_orig_file normalize $p]]}
proc file {sub args} {
 if {$sub eq "copy"} {
  set src [lindex $args end-1];set dst [lindex $args end]
  if {[lsearch -exact $::audit_allowed [audit_key $dst]]<0} {error "WRITE_GUARD target $dst"}
  if {[string first [audit_key $::audit_local] [audit_key $src]]!=0} {error "WRITE_GUARD source $src"}
  puts $::audit_log [list COPY $src $dst];flush $::audit_log
 } elseif {$sub eq "delete"} {
  if {[llength $args]!=2 || [lindex $args 0] ne "-force" || [audit_key [lindex $args 1]] ne [audit_key {D:/vivado18.3/Vivado/2018.3/data/parts/xilinx/zynq/devint/zynq.rtd.bak}]} {error "WRITE_GUARD delete $args"}
  puts $::audit_log [list DELETE [lindex $args 1]];flush $::audit_log
 } elseif {[lsearch -exact {rename mkdir attributes mtime atime link} $sub]>=0} {error "WRITE_GUARD file $sub $args"}
 return [eval [linsert $args 0 audit_orig_file $sub]]
}
rename open audit_orig_open
proc open {path args} {
 set mode r
 if {[llength $args]>0} {set mode [lindex $args 0]}
 if {$mode ne "r" && $mode ne "rb"} {error "WRITE_GUARD direct open $path $mode"}
 return [eval [linsert $args 0 audit_orig_open $path]]
}
foreach cmd {exec load create_project open_project set_property set_param} {
 if {[llength [info commands $cmd]]} {rename $cmd audit_original_$cmd;proc $cmd args {error "WRITE_GUARD external or configuration command"}}
}
if {[catch {
 source {D:/FPGACompetitionProject/.local/hdmi-vivado2018-20261016-r2/kit/ip_patch/all_src_files.tcl}
 if {[version -short] ne "2018.3"} {error "Wrong Vivado version"}
 if {[audit_key [get_vvd_path]] ne [audit_key {D:/vivado18.3/Vivado/2018.3}]} {error "Wrong tool installation root"}
 if {![file exists {D:/vivado18.3/Vivado/2018.3/data/parts/xilinx/common/unisim.btl}]} {error "Require actual 2018.3 reset branch"}
 puts "ACTUAL_PATCH_D:/vivado18.3/Vivado/2018.3 [get_vvd_path]"
 replace_7z030ai_file 0
 puts "INPLACE_ORIGINAL_030AI_PATCH_COMPLETE"
} result]} {puts "INPLACE_PATCH_FAILED $result";puts $audit_log "FAILED $result";close $audit_log;exit 1}
close $audit_log
exit
