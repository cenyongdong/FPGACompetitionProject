# Restore the four original ai7030.xdc clock exceptions that were read before
# the exported factory PS checkpoint's FCLK root existed (lines 11,12,24,25).
# Preserve their legacy scope only. HDMI and all diagnostic blocks remain
# timed by their explicit CDC constraints; no new clock pair is exempted.
set factory_gp [get_clocks -of_objects [get_pins U0_ps_ai_peripheral/ps_ai_wrapper_u0/clk_wiz_0_inst/inst/plle2_adv_inst/CLKOUT0]]
set factory_out2 [get_clocks -quiet clk_out2_clk_wiz_0]
set factory_rx [get_clocks rx_sdi_inst/SDI0/SDI/GTX_i/gtxe2_i/RXOUTCLK]
foreach c [list $factory_gp $factory_rx] {
 if {[llength $c]!=1} {error "Factory clock binding is not unique: $c"}
}
foreach pair [list [list $factory_gp $factory_out2] [list $factory_out2 $factory_gp] [list $factory_gp $factory_rx] [list $factory_rx $factory_gp]] {
 lassign $pair launch capture
 if {![llength $launch] || ![llength $capture]} {
  puts "FACTORY_CLOCK_UNUSED $launch $capture"
  continue
 }
 set legacy_launch [filter [all_registers -clock $launch -clock_pins] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/*}]
 set legacy_cells [filter [all_registers -clock $capture -cells] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/*}]
 set legacy_inputs [get_pins -of_objects $legacy_cells -filter {DIRECTION == IN && IS_CLOCK == 0}]
 if {![llength $legacy_launch] || ![llength $legacy_inputs]} {
  puts "FACTORY_CLOCK_UNUSED $launch $capture"
  continue
 }
 # A clock source and legacy destination collection avoid the Cartesian
 # launch/through expansion. First prove that no protected launch reaches
 # those destinations, so this cannot exempt any added diagnostic path.
 set protected_launch [filter [all_registers -clock $launch -cells] {NAME =~ U0_ps_ai_peripheral/hdmi_display/* || NAME =~ U0_ps_ai_peripheral/ai_path_monitor/* || NAME =~ U0_ps_ai_peripheral/ai_read_path_monitor/*}]
 set protected_q {}
 if {[llength $protected_launch]} {set protected_q [get_pins -of_objects $protected_launch -filter {DIRECTION == OUT}]}
 set legacy_names [dict create]
 foreach p $legacy_inputs {dict set legacy_names [get_property NAME $p] 1}
 if {[llength $protected_q]} {
  foreach p [all_fanout -flat -endpoints_only -from $protected_q] {
   if {[dict exists $legacy_names [get_property NAME $p]]} {error "Protected launch reaches factory exception: $p"}
  }
 }
 set_max_delay -reset_path -datapath_only [get_property PERIOD $capture] -from $launch -to $capture
 set_false_path -from $launch -to $legacy_inputs
 puts "FACTORY_CLOCK_REBOUND $launch $capture launch=[llength $legacy_launch] capture=[llength $legacy_inputs] protected_to_legacy=0"
}
