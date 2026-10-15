set out [file normalize {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-system-20261015-r1}]
if {[catch {
 create_project hdmi_ip_status {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/project} -part xc7z030ffg676-2
 set_property ip_repo_paths [list {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/PS_AI IP}] [current_project]
 set_property ip_cache_permissions {} [current_project]
 update_ip_catalog
 foreach ip [list {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {read_ip $ip}
 add_files -norecurse {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 open_bd_design {D:/FPGACompetitionProject/.local/hdmi-system-20261015-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
 report_ip_status -file [file join $out IP-status.rpt]
 foreach ip [get_ips -all] {
  puts "IP_STATUS|$ip|[get_property IPDEF $ip]|[get_property IS_LOCKED $ip]|[get_property IP_FILE $ip]"
 }
 puts "SYSTEM_IP_STATUS_COMPLETE"
 close_project
} result]} {puts "SYSTEM_IP_STATUS_FAIL $result";exit 1}
exit
