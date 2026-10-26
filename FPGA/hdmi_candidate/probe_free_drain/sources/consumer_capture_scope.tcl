# Retain the r45 functional-consumer scope of the inherited GP->HP exception.
# Only legacy captures remain exempt; consumer captures retain their 5 ns bound.
set raw_gp [get_clocks clk_out1_clk_wiz_0]
set raw_hp [get_clocks clk_pll_i]
set raw_old_launch [filter [all_registers -clock $raw_gp -clock_pins] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set raw_old_capture [filter [all_registers -clock $raw_hp -cells] {NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set raw_old_inputs [get_pins -of_objects $raw_old_capture -filter {DIRECTION == IN && IS_CLOCK == 0}]
if {![llength $raw_old_launch] || ![llength $raw_old_inputs]} {error "PS_RELEASE_RAW_LEGACY_SCOPE_MISSING"}
set_max_delay -reset_path -datapath_only 5.000 -from $raw_old_launch -to $raw_hp
# These are sequential data/control endpoints, so -to preserves the exact
# legacy scope without a large launch/through Cartesian expansion.
set_false_path -from $raw_old_launch -to $raw_old_inputs

puts "FUNCTIONAL_CONSUMER_FACTORY_CUT_SCOPE_RESTORED"
set consumer_raw [get_cells -quiet -hier -regexp {^U0_ps_ai_peripheral/deferred_control/held_flags_reg\[[0-9]+\]$}]
set consumer_raw_d [get_pins -of_objects $consumer_raw -filter {REF_PIN_NAME == D}]
if {![llength $consumer_raw_d]} {error "Functional raw status capture missing"}
set_max_delay -datapath_only 5.000 -from [all_fanin -flat -startpoints_only -to $consumer_raw_d] -to $consumer_raw_d
puts "FUNCTIONAL_CONSUMER_RAW_BOUND [llength $consumer_raw_d] endpoints 5ns"
