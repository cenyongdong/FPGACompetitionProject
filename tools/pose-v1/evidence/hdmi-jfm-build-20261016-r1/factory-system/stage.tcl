
if {[catch {
 open_project {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 foreach name [list {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-jfm-build-20261016-r1/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {
  puts "CREATE_OWNER_OOC_RUN $name"
  create_ip_run [get_files -all $name]
 }
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/runs-before.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property DIRECTORY $r]"}
 close $f
 launch_runs impl_1 -to_step write_bitstream -jobs 1
 wait_on_run impl_1
 set status [get_property STATUS [get_runs impl_1]]
 puts "FACTORY_SYSTEM_RUN_STATUS $status"
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/runs-after.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property PROGRESS $r]"}
 close $f
 if {![string match {*Complete*} $status]} {error "Factory implementation did not complete"}
 open_run impl_1
 report_timing_summary -report_unconstrained -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/timing-summary.rpt}
 report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/DRC.rpt}
 report_methodology -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/methodology.rpt}
 report_clock_interaction -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/clock-interaction.rpt}
 report_cdc -details -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/CDC.rpt}
 report_utilization -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/utilization.rpt}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1/factory-system/GT-and-rule-state.txt} w]
 foreach c [get_cells -hier -filter {REF_NAME =~ GTXE2* || REF_NAME =~ GTHE2*}] {puts $f "GT|$c|[get_property REF_NAME $c]"}
 foreach n {REQP-44 REQP-46 REQP-52 REQP-56} {puts $f "RULE|$n|[get_property IS_ENABLED [get_drc_checks $n]]|[get_property SEVERITY [get_drc_checks $n]]"}
 puts $f "PART|[get_property PART [current_design]]"
 close $f
 close_project
 puts "FACTORY_SYSTEM_CHAIN_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "FACTORY_SYSTEM_FAILED $result";puts $::errorInfo;exit 1}
exit
