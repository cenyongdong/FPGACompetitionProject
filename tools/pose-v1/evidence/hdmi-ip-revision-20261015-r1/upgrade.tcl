set out [file normalize {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ip-revision-20261015-r1}]
proc dump_ips {dest} {
 set f [open $dest w]
 foreach ip [lsort [get_ips -all]] {
  foreach prop [concat {IPDEF IS_LOCKED} [lsort [list_property $ip CONFIG.*]]] {
   set val [get_property $prop $ip];binary scan [encoding convertto utf-8 $val] H* h
   puts $f "$ip\t$prop\t$h"
  }
 }
 close $f
}
if {[catch {
 create_project hdmi_revision {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/project} -part xc7z030ffg676-2
 set_property ip_repo_paths [list {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {read_ip $ip}
 add_files -norecurse {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 open_bd_design {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 dump_ips [file join $out config-before.tsv]
 save_bd_design
 file copy {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd} [file join $out bd-before-tool.json]
 set whitelist [list afifo_16i_64o_largebuf afifo_24w_4096d afifo_64i_16o_128 clk_wiz_0 cmos_clkgen_742_5 fifo_1 mgtclk mig_7series_0 mna_idfifo_w12 rindex_buf_2b_16w sys_clk windex_buf_2b_16w]
 foreach name $whitelist {
  set ip [get_ips $name]
  if {[llength $ip]!=1 || ![get_property IS_LOCKED $ip]} {error "Unexpected whitelist/lock $name"}
  puts "REVISION_UPGRADE_ROOT $name [get_property IPDEF $ip]"
  upgrade_ip $ip
 }
 set cells {}
 foreach cell [get_bd_cells -hier] {
  set v [get_property VLNV $cell]
  if {$v=="xilinx.com:ip:axi_interconnect:2.1" || $v=="xilinx.com:ip:xlconcat:2.1"} {lappend cells $cell}
 }
 if {[llength $cells]!=4} {error "Unexpected BD whitelist count $cells"}
 puts "REVISION_UPGRADE_BD $cells"
 upgrade_bd_cells $cells
 dump_ips [file join $out config-after.tsv]
 report_ip_status -file [file join $out IP-status-after.rpt]
 save_bd_design
 file copy {D:/FPGACompetitionProject/.local/hdmi-ip-revision-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd} [file join $out bd-after-tool.json]
 close_project
 puts "REVISION_UPGRADE_COMPLETE_NO_GENERATION"
} result]} {puts "REVISION_UPGRADE_FAIL $result";exit 1}
exit
