
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 foreach name [list {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {
  set owner [get_files -all -quiet $name]
  if {[llength $owner]!=1} {error "Expected exact root owner $name"}
  puts "GENERATE_ORIGINAL_ROOT_OWNER $name"
  generate_target all $owner
 }
 close_project
 puts "ORIGINAL_ROOT_OWNED_GENERATION_COMPLETE"
} result]} {puts "ROOT_GENERATION_FAILED $result";puts $::errorInfo;exit 1}
exit
