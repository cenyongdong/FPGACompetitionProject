set old_gp [filter [all_registers -clock [get_clocks clk_out1_clk_wiz_0] -clock_pins] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set consumer_cells [get_cells -quiet -hier -filter {NAME =~ U0_ps_ai_peripheral/deferred_control/* || NAME =~ U0_ps_ai_peripheral/startup_drain/*}]
set consumer_ends [get_pins -of_objects $consumer_cells -filter {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
set old_gp_q [get_pins -of_objects [get_cells -of_objects $old_gp] -filter {DIRECTION == OUT}]
set old_gp_ends [filter [all_fanout -flat -endpoints_only -from $old_gp_q] {NAME =~ U0_ps_ai_peripheral/deferred_control/* || NAME =~ U0_ps_ai_peripheral/startup_drain/*}]
set tested_gp_ends {}
set old_gp_names [dict create]
foreach pin $old_gp {dict set old_gp_names [get_property NAME $pin] 1}
foreach endpoint $old_gp_ends {
 if {[get_property REF_PIN_NAME $endpoint] ni {D CE}} {continue}
 set clock_pins [get_pins -of_objects [get_cells -of_objects $endpoint] -filter {REF_PIN_NAME == C}]
 set capture_clocks [get_clocks -of_objects $clock_pins]
 if {[lsearch -exact $capture_clocks clk_pll_i]<0} {continue}
 # all_fanout also follows clock-generation cells in the legacy collection.
 # Intersect the actual data-cone startpoints to exclude clock-tree reachability;
 # a nonexistent legacy data path must not be reported as a hidden false path.
 set actual_launch {}
 foreach pin [all_fanin -flat -startpoints_only -to $endpoint] {
  if {[dict exists $old_gp_names [get_property NAME $pin]]} {lappend actual_launch $pin}
 }
 if {![llength $actual_launch]} {continue}
 lappend tested_gp_ends $endpoint
 set p [get_timing_paths -from $actual_launch -to $endpoint -max_paths 1]
 if {![llength $p]} {error "Inherited GP cut hides functional consumer endpoint: $endpoint"}
 set requirement [get_property REQUIREMENT $p];set slack [get_property SLACK $p]
 puts $f "CONSUMER_GP\t$endpoint\t$requirement\t$slack"
 if {abs($requirement-5)>0.001 || $slack<0} {error "Consumer GP path fails: $endpoint"}
}
puts $f "CONSUMER_GP_ENDPOINTS\t[llength $tested_gp_ends]"

# PS RVALID is retained only as a functional completion condition.
set ps_flags [get_cells -quiet -hier -regexp {^U0_ps_ai_peripheral/deferred_control/held_flags_reg\[16\]$}]
set ps_flag_d [get_pins -of_objects $ps_flags -filter {REF_PIN_NAME == D}]
if {[llength $ps_flag_d]!=1} {error "Functional PS return flag missing"}
set p [get_timing_paths -to $ps_flag_d -max_paths 1]
if {![llength $p]} {error "Functional PS return flag untimed"}
set r [get_property REQUIREMENT $p];set slack [get_property SLACK $p]
puts $f "CONSUMER_PS_RVALID\t$r\t$slack"
if {abs($r-5)>0.001 || $slack<0} {error "Functional PS return flag timing failed"}
