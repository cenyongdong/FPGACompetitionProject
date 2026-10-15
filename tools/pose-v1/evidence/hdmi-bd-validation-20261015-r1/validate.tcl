set out [file normalize {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-bd-validation-20261015-r1}]
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
 create_project hdmi_bd_validation {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/project} -part xc7z030ffg676-2
 set_property ip_repo_paths [list {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {read_ip $ip}
 add_files -norecurse {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 open_bd_design {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 dump_ips [file join $out config-opened.tsv]
 puts "BD_VALIDATE_BEGIN_NO_GENERATION"
 validate_bd_design
 dump_ips [file join $out config-validated.tsv]
 save_bd_design
 file copy {D:/FPGACompetitionProject/.local/hdmi-bd-validation-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd} [file join $out bd-validated.json]
 report_ip_status -file [file join $out IP-status.rpt]
 close_project
 puts "BD_VALIDATE_COMPLETE_NO_GENERATION"
} result]} {puts "BD_VALIDATE_FAIL $result";exit 1}
exit
