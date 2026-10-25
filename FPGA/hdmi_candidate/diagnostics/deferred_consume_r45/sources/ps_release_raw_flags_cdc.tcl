# The HP first-event record samples raw reset/status pins for diagnostics.
# Narrow the inherited GP->HP cut only for this new record; retain all old cuts.
set raw_gp [get_clocks clk_out1_clk_wiz_0]
set raw_hp [get_clocks clk_pll_i]
set raw_old_launch [filter [all_registers -clock $raw_gp -clock_pins] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/* && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_observer/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set raw_old_capture [filter [all_registers -clock $raw_hp -cells] {NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/release_history/* && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_observer/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set raw_old_inputs [get_pins -of_objects $raw_old_capture -filter {DIRECTION == IN && IS_CLOCK == 0}]
if {![llength $raw_old_launch] || ![llength $raw_old_inputs]} {error "PS_RELEASE_RAW_LEGACY_SCOPE_MISSING"}
set_max_delay -reset_path -datapath_only 5.000 -from $raw_old_launch -to $raw_hp
# These are sequential data/control endpoints, so -to preserves the exact
# legacy scope without a large launch/through Cartesian expansion.
set_false_path -from $raw_old_launch -to $raw_old_inputs
set raw_flags [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/first_r_levels_reg\[[0-9]+\]$}]
# Reserved input bit7 is hardwired zero; pre-opt can still retain its register.
set raw_dynamic {}
foreach c $raw_flags {
 if {![regexp {first_r_levels_reg\[7\]$} [get_property NAME $c]]} {lappend raw_dynamic $c}
}
set raw_flags $raw_dynamic
set raw_D [get_pins -of_objects $raw_flags -filter {REF_PIN_NAME == D}]
if {[llength $raw_D]<16} {error "PS_RELEASE_RAW_FLAGS_MISSING"}
set raw_starts [all_fanin -flat -startpoints_only -to $raw_D]
set_max_delay -datapath_only 5.000 -from $raw_starts -to $raw_D
foreach pin $raw_D {
 set path [get_timing_paths -to $pin -max_paths 1]
 if {![llength $path] || [get_property REQUIREMENT $path] eq "" || abs([get_property REQUIREMENT $path]-5)>0.001} {error "PS_RELEASE_RAW_FLAG_PATH_CUT $pin"}
}
puts "PS_RELEASE_RAW_FLAGS_BOUND bits=[llength $raw_D] datapath_ns=5.000"
