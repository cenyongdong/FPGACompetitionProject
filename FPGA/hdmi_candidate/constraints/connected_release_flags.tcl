# Same one-HP-period data bound as the other release witness inputs.
# The connected S01 restores flags 10 (ARVALID), 12 (AWVALID), 13 (WVALID).
# No clock/frequency/false-path change; both GP synchronizer and raw HP capture
# must remain timed. Apply before implementation, or before post-route signoff.
set connected_release_root {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/}
foreach stem {levels_meta first_r_levels} {
 set pins {}
 foreach bit {10 12 13} {
  set cells [get_cells -quiet -hier -regexp [format {%s%s_reg\[%d\]$} $connected_release_root $stem $bit]]
  if {[llength $cells]!=1} {error "Connected release flag missing: $stem bit$bit"}
  lappend pins [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
 }
 set starts [all_fanin -flat -startpoints_only -to $pins]
 if {![llength $starts]} {error "Connected release flag source missing: $stem"}
 set_max_delay -datapath_only 5.000 -from $starts -to $pins
 puts "CONNECTED_RELEASE_FLAGS_BOUND $stem [llength $pins] 5.000"
}
