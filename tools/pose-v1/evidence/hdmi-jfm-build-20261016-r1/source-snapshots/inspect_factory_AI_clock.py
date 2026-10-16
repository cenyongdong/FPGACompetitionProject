"""Read-only trace of the actual 1 GHz AI clock causing minimum-period failures."""
import vivado2018_support as s
R=s.R;s.E=R/'tools/pose-v1/evidence/hdmi-jfm-build-20261016-r1';s.W=R/'.local/hdmi-jfm-build-20261016-r1'
tcl=r'''
if {[catch {
 open_checkpoint {REF/fpai_demo_vivado.runs/impl_r2/ai7030_edif_top_routed.dcp}
 set pll [get_cells -quiet U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/plle2_adv_inst]
 set buf [get_cells -quiet U0_ps_ai_peripheral/ZGolo/u_AI_Mate_top/clkrst_wrapper_u0/AI_CORE_CLK/inst/clkout1_buf]
 if {[llength $pll]!=1 || [llength $buf]!=1} {error "Exact AI clock cells missing"}
 report_property -all -file {@@OUT@@/PLL-properties.txt} $pll
 report_property -all -file {@@OUT@@/BUFG-properties.txt} $buf
 set f [open {@@OUT@@/actual-clock-connectivity.txt} w]
 foreach c [get_clocks -of_objects [get_pins $pll/CLKOUT0]] {
  puts $f "CLOCK|$c|PERIOD=[get_property PERIOD $c]|WAVEFORM=[get_property WAVEFORM $c]"
 }
 foreach pin [list $pll/CLKOUT0 $buf/O] {
  puts $f "DRIVER $pin"
  foreach p [get_pins -leaf -of_objects [get_nets -segments -of_objects [get_pins $pin]]] {
   puts $f "PIN|$p|[get_property DIRECTION $p]"
  }
 }
 close $f
 close_design
 puts "ACTUAL_AI_CLOCK_READ_ONLY_INSPECTION_COMPLETE"
} result]} {puts "AI_CLOCK_INSPECTION_FAILED $result";puts $::errorInfo;exit 1}
exit
'''.replace('REF',s.W.as_posix()+'/reference')
s.stage('AI-clock-trace',tcl,budget=180)
