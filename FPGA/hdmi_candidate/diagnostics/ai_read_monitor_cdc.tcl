# Procedural constraints, sourced after hdmi_cdc.tcl and ai_monitor_cdc.tcl.
# Scope: only the new ai_read_path_monitor. No original AI/DDR waiver changes.
if {[info exists ::ai_read_monitor_cdc_applied]} {error "AI_READ_MONITOR_CDC_LOADED_TWICE"}
set ::ai_read_monitor_cdc_applied 1
if {![info exists ::hdmi_cdc_constraints_applied]} {error "AI_READ_MONITOR_SCOPE_NOT_PREPARED"}
proc ai_read_mon_cells {relative minimum} {
 set cells [get_cells -quiet -hier -regexp "^U0_ps_ai_peripheral/ai_read_path_monitor/$relative\$"]
 if {[llength $cells]<$minimum} {error "AI_READ_MONITOR_OBJECTS_MISSING $relative [llength $cells]"}
 return $cells
}
proc ai_read_mon_pins {cells pin} {
 set pins [get_pins -quiet -of_objects $cells -filter "REF_PIN_NAME == $pin"]
 if {[llength $pins]!=[llength $cells]} {error "AI_READ_MONITOR_PIN_CONTRACT $pin"}
 return $pins
}
proc ai_read_mon_indices {cells} {
 set indices {}
 foreach cell $cells {
  if {![regexp {\[([0-9]+)\]$} [get_property NAME $cell] unused index]} {error "AI_READ_MONITOR_INDEX_MISSING $cell"}
  lappend indices $index
 }
 return [lsort -integer -unique $indices]
}
# Constants in the 104-word bank may be removed. Require matching surviving
# indices, not merely the same number of bits; no bit may exceed word103.
set ai_read_source [ai_read_mon_cells {source_snapshot_reg\[[0-9]+\]} 1024]
set ai_read_capture [ai_read_mon_cells {csr_snapshot_reg\[[0-9]+\]} 1024]
set ai_read_source_indices [ai_read_mon_indices $ai_read_source]
set ai_read_capture_indices [ai_read_mon_indices $ai_read_capture]
if {$ai_read_source_indices ne $ai_read_capture_indices || [llength $ai_read_source]>3328 ||
    [llength $ai_read_source_indices]!=[llength $ai_read_source] ||
    [lindex $ai_read_source_indices end]>=3328} {error "AI_READ_MONITOR_SNAPSHOT_INDEX_CONTRACT"}
set ai_read_source_C [ai_read_mon_pins $ai_read_source C]
set ai_read_capture_C [ai_read_mon_pins $ai_read_capture C]
set ai_read_capture_D [ai_read_mon_pins $ai_read_capture D]
set ai_read_source_clocks [get_clocks -of_objects $ai_read_source_C]
set ai_read_capture_clocks [get_clocks -of_objects $ai_read_capture_C]
if {[llength $ai_read_source_clocks]!=1 || [llength $ai_read_capture_clocks]!=1} {error "AI_READ_MONITOR_CLOCK_UNCERTAIN"}
set ai_read_source_period [get_property PERIOD $ai_read_source_clocks]
set ai_read_capture_period [get_property PERIOD $ai_read_capture_clocks]
if {abs($ai_read_source_period-5.000)>0.001 || abs($ai_read_capture_period-10.000)>0.001} {error "AI_READ_MONITOR_CLOCK_CONTRACT"}
set_max_delay -datapath_only 10.000 -from $ai_read_source_C -to $ai_read_capture_D
foreach relative {{arm_request_sync_reg\[0\]} {freeze_request_sync_reg\[0\]} {arm_ack_sync_reg\[0\]} {freeze_ack_sync_reg\[0\]}} {
 set cells [ai_read_mon_cells $relative 1]
 if {[llength $cells]!=1} {error "AI_READ_MONITOR_FIRST_STAGE_NOT_UNIQUE $relative"}
 set_false_path -to [ai_read_mon_pins $cells D]
 puts "AI_READ_MONITOR_FIRST_STAGE_ASYNC_D $cells"
}
foreach relative {{source_release_reg\[[0-9]+\]} {csr_release_reg\[[0-9]+\]}} {
 set cells [ai_read_mon_cells $relative 3]
 if {[llength $cells]!=3} {error "AI_READ_MONITOR_RESET_CHAIN_CONTRACT $relative"}
 set_false_path -to [ai_read_mon_pins $cells CLR]
 puts "AI_READ_MONITOR_RESET_RELEASE_CLR_ONLY $relative bits=3"
}
set ai_read_paths [get_timing_paths -from $ai_read_source_C -to $ai_read_capture_D -max_paths 1]
if {![llength $ai_read_paths]} {error "AI_READ_MONITOR_BUS_PATH_CUT_OR_ABSENT"}
set ai_read_requirement [get_property REQUIREMENT [lindex $ai_read_paths 0]]
if {abs($ai_read_requirement-10.000)>0.001} {error "AI_READ_MONITOR_BUS_BOUND_WRONG $ai_read_requirement"}
puts "AI_READ_MONITOR_STABLE_BUS_ACTIVE source_bits=[llength $ai_read_source] capture_bits=[llength $ai_read_capture] max_ns=$ai_read_requirement source_period=$ai_read_source_period capture_period=$ai_read_capture_period"
