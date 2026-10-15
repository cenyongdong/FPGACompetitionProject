set out [file normalize {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ip-generation-20261015-r3}]
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

open_project {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/project/hdmi_bounded.xpr}
open_bd_design {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}
dump_ips [file join $out config-before-generation.tsv]
puts "TARGET_GENERATION_BEGIN"
foreach path [list {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/sdi/ip/smpte_sdi/smpte_sdi.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/sdi/ip/mgtclk/mgtclk.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/sdi/ip/sys_clk/sys_clk.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/mig_7series_0/mig_7series_0.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/clk_wiz_0/clk_wiz_0.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/afifo_24w_4096d/afifo_24w_4096d.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/rindex_buf_2b_16w/rindex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/windex_buf_2b_16w/windex_buf_2b_16w.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/afifo_64i_16o_128/afifo_64i_16o_128.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/fifo_1/fifo_1.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/afifo_16i_64o_largebuf/afifo_16i_64o_largebuf.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/cmos_clkgen_742_5/cmos_clkgen_742_5.xci} {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/rtl/ip/mna_idfifo_w12/mna_idfifo_w12.xci}] {
 puts "GENERATE_STANDALONE $path"
 generate_target all [get_files $path]
}
puts "GENERATE_BD_SYSTEM"
generate_target all [get_files {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ps_ai.bd}]
dump_ips [file join $out config-after-generation.tsv]
report_ip_status -file [file join $out IP-status-after-generation.rpt]
set files [get_files -compile_order sources -used_in synthesis]
set f [open [file join $out synthesis-files.txt] w]
foreach path $files {puts $f $path}
close $f
save_project_as hdmi_generated {D:/FPGACompetitionProject/.local/hdmi-ip-generation-20261015-r3/generated-project}
close_project
puts "BOUNDED_TARGET_GENERATION_COMPLETE"

} result]} {puts "STAGE_FAIL $result";exit 1}
exit
