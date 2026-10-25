# The inherited HDMI-era pin->clock cuts include the later HP2 diagnostics.
# Remove only their launch-pin subset, using the same pin->clock form as the
# inherited cut. Legacy launch pins and original clock-pair scopes are intact.
# No false path is added. Reinstall the original explicit 5/10 ns bounds.
foreach pair {{clk_out1_clk_wiz_0 clk_pll_i} {clk_pll_i clk_out1_clk_wiz_0}} {
 set launch [get_clocks [lindex $pair 0]]
 set capture [get_clocks [lindex $pair 1]]
 if {[llength $launch]!=1 || [llength $capture]!=1} {error "HP2 inherited clock pair missing: $pair"}
 set added_launch [filter [all_registers -clock $launch -clock_pins] {NAME =~ U0_ps_ai_peripheral/hp2_cycle_recorder/* || NAME =~ U0_ps_ai_peripheral/hp2_protocol_recorder/* || NAME =~ U0_ps_ai_peripheral/hp2_protocol_observer/*}]
 if {![llength $added_launch]} {error "HP2 diagnostic launch pins missing: $pair"}
 set_max_delay -reset_path -datapath_only [get_property PERIOD $capture] -from $added_launch -to $capture
 puts "HP2_INHERITED_CUT_DIAGNOSTIC_SUBSET_REMOVED $pair count=[llength $added_launch]"
}
source [file join [file dirname [info script]] hp2_cycle_trace_cdc.tcl]
source [file join [file dirname [info script]] hp2_protocol_cdc.tcl]
# A bound must be effective on every new first-stage status/raw endpoint.
foreach p [lsort -unique [concat $trace_meta_D $pmD $rawD $pe]] {
 set t [get_timing_paths -to $p -max_paths 1]
 set r [get_property REQUIREMENT $t]
 if {![string is double -strict $r] || abs($r-5)>0.001} {error "HP2 first-stage bound absent/cut: $p requirement=$r"}
}
