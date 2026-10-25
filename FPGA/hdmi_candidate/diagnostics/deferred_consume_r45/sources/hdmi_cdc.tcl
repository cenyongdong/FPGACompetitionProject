# Procedural Tcl: source from the implementation pre-opt hook, NOT read_xdc.
# Scoped to the new HDMI hierarchy; no global asynchronous clock-group cuts.
# Source pointer Gray buses are registered. Mailbox data stays fixed until the
# synchronized acknowledgement returns; source/target have coordinated resets.
if {![info exists ::hdmi_cdc_constraints_applied]} {
 set ::hdmi_cdc_constraints_applied 1
 proc hdmi_cdc_cells {relative min_count} {
  set found [get_cells -quiet -hier -regexp "^U0_ps_ai_peripheral/hdmi_display/$relative\$"]
  if {[llength $found] < $min_count} {error "HDMI_CDC_OBJECTS_MISSING $relative count=[llength $found]"}
  return $found
 }
 proc hdmi_cdc_pins {cells pin} {return [get_pins -of_objects $cells -filter "REF_PIN_NAME == $pin"]}
 proc hdmi_cdc_period {cell} {
  set clocks [get_clocks -of_objects [hdmi_cdc_pins $cell C]]
  if {[llength $clocks]!=1} {error "HDMI_CDC_CLOCK_UNCERTAIN $cell $clocks"}
  return [get_property PERIOD $clocks]
 }
 # The factory CSR <-> DDR clock cuts would also cover the new mailbox.
 # Replace exactly those two cuts with their original launch-clock pins,
 # excluding only the new HDMI hierarchy. Keep every old launch path cut;
 # new HDMI crossings retain the explicit bounds/synchronizers below.
 foreach pair {{clk_out1_clk_wiz_0 clk_pll_i} {clk_pll_i clk_out1_clk_wiz_0}} {
  set launch [get_clocks [lindex $pair 0]]
  set capture [get_clocks [lindex $pair 1]]
  if {[llength $launch]!=1 || [llength $capture]!=1} {error "HDMI_FACTORY_CLOCK_PAIR_MISSING $pair"}
  set all_launch [all_registers -clock $launch -clock_pins]
  set old_launch [filter $all_launch {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/* && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_observer/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
  set new_launch [filter $all_launch {NAME =~ U0_ps_ai_peripheral/hdmi_display/* || NAME =~ U0_ps_ai_peripheral/ai_path_monitor/* || NAME =~ U0_ps_ai_peripheral/ai_read_path_monitor/* || NAME =~ U0_ps_ai_peripheral/hp2_cycle_recorder/* || NAME =~ U0_ps_ai_peripheral/hp2_protocol_recorder/* || NAME =~ U0_ps_ai_peripheral/hp2_protocol_observer/* || NAME =~ U0_ps_ai_peripheral/deferred_control/* || NAME =~ U0_ps_ai_peripheral/startup_drain/*}]
  if {![llength $old_launch] || ![llength $new_launch]} {error "HDMI_CUT_SCOPE_EMPTY $pair"}
  set_max_delay -reset_path -datapath_only [get_property PERIOD $capture] -from $launch -to $capture
  set_false_path -from $old_launch -to $capture
  puts "HDMI_FACTORY_CUT_SCOPED $pair old_launch_pins=[llength $old_launch] new_launch_pins=[llength $new_launch]"
 }
 proc hdmi_gray_bound {source target expected} {
  set src [hdmi_cdc_cells $source $expected]
  set dst [hdmi_cdc_cells $target $expected]
  if {[llength $src]!=$expected || [llength $dst]!=$expected} {error "HDMI_GRAY_WIDTH $source $target"}
  set period [hdmi_cdc_period [lindex $src 0]]
  set q [hdmi_cdc_pins $src C];set d [hdmi_cdc_pins $dst D]
  set_max_delay -datapath_only $period -from $q -to $d
  set_bus_skew $period -from $q -to $d
  puts "HDMI_GRAY_BOUND $source -> $target bits=$expected max_delay_and_skew_ns=$period"
 }
 hdmi_gray_bound {scanout/fifo/wr_gray_reg\[[0-9]+\]} {scanout/fifo/wr_sync1_reg\[[0-9]+\]} 10
 hdmi_gray_bound {scanout/fifo/rd_gray_reg\[[0-9]+\]} {scanout/fifo/rd_sync1_reg\[[0-9]+\]} 10
 hdmi_gray_bound {pixel_gray_reg\[[0-9]+\]} {pixel_gray_csr1_reg\[[0-9]+\]} 32
 # Only the intentional single-bit synchronizer first D pin is asynchronous.
 # Second/third stages retain ordinary same-clock setup and hold checks.
 foreach path {
  {scanout/core/core/mailbox/request_sync_reg\[0\]}
  {scanout/core/core/mailbox/response_sync_reg\[0\]}
  {scanout/core/core/control/locked_sync_reg\[0\]}
  {scanout/core/core/control/frame_sync_reg\[0\]}
  {scanout/core/core/control/sink_sync_reg\[0\]}
  {scanout/pixels/run_sync_reg\[0\]}
  {scanout/pixels/idle_sync_reg\[0\]}
  {locked_csr_reg\[0\]} {idle_csr_reg\[0\]} {pattern_pixel_reg\[0\]}
 } {
  set c [hdmi_cdc_cells $path 1]
  if {[llength $c]!=1} {error "HDMI_FIRST_STAGE_NOT_UNIQUE $path"}
  set_false_path -to [hdmi_cdc_pins $c D]
  puts "HDMI_FIRST_STAGE_ASYNC_D $c"
 }
 # Intentional asynchronous inputs to three-stage reset-release chains only.
 # All functional pointer/lane/Gray state uses the LOCAL synchronized reset;
 # its recovery/removal checks and every release-chain D path remain timed.
 foreach path {{pixel_release_reg\[[0-9]+\]} {scanout/fifo/wr_release_reg\[[0-9]+\]} {scanout/fifo/rd_release_reg\[[0-9]+\]}} {
  set cells [hdmi_cdc_cells $path 3]
  set clear [hdmi_cdc_pins $cells CLR]
  if {[llength $cells]!=3 || [llength $clear]!=3} {error "HDMI_RESET_RELEASE_WIDTH_OR_PIN $path"}
  set_false_path -to $clear
  puts "HDMI_ASYNC_RESET_CHAIN_INPUT_ONLY $path bits=3"
 }
 set command [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
 set response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
 set capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
 set mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $response 0] C]]
 set csr_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $command 0] C]]
 set memory_regs [filter [all_registers -clock $mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set memory_period [hdmi_cdc_period [lindex $response 0]]
 set csr_period [hdmi_cdc_period [lindex $command 0]]
 set_max_delay -datapath_only $memory_period -from [hdmi_cdc_pins $command C] -to [hdmi_cdc_pins $memory_regs D]
 set_max_delay -datapath_only $csr_period -from [hdmi_cdc_pins $response C] -to [hdmi_cdc_pins $capture D]
 puts "HDMI_MAILBOX_STABLE_BUS command_bits=[llength $command] max_ns=$memory_period response_bits=[llength $response] max_ns=$csr_period"
}
