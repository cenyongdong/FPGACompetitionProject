# Apply after the scoped factory CSR/DDR clock-pair exceptions in hdmi_cdc.tcl.
# Only the new diagnostic endpoint is covered; no AI or DDR exception changes.
if {[info exists ::ai_monitor_cdc_applied]} {error "AI monitor constraints loaded twice"}
set ::ai_monitor_cdc_applied 1
proc ai_mon_cells {relative minimum} {
 set c [get_cells -quiet -hier -regexp "^U0_ps_ai_peripheral/ai_path_monitor/$relative\$"]
 if {[llength $c]<$minimum} {error "AI_MONITOR_OBJECTS_MISSING $relative [llength $c]"}
 return $c
}
set ai_source [ai_mon_cells {source_snapshot_reg\[[0-9]+\]} 128]
set ai_capture [ai_mon_cells {csr_snapshot_reg\[[0-9]+\]} 128]
set ai_source_clocks [get_clocks -of_objects [hdmi_cdc_pins $ai_source C]]
set ai_capture_clocks [get_clocks -of_objects [hdmi_cdc_pins $ai_capture C]]
if {[llength $ai_source_clocks]!=1 || [llength $ai_capture_clocks]!=1} {error "AI_MONITOR_CLOCK_UNCERTAIN"}
set ai_source_period [get_property PERIOD $ai_source_clocks]
set ai_capture_period [get_property PERIOD $ai_capture_clocks]
if {abs($ai_source_period-5.000)>0.001 || abs($ai_capture_period-10.000)>0.001} {error "AI_MONITOR_CLOCK_CONTRACT"}
set_max_delay -datapath_only $ai_capture_period -from [hdmi_cdc_pins $ai_source C] -to [hdmi_cdc_pins $ai_capture D]
foreach relative {{request_sync_reg\[0\]} {ack_sync_reg\[0\]}} {
 set c [ai_mon_cells $relative 1]
 if {[llength $c]!=1} {error "AI_MONITOR_FIRST_STAGE_NOT_UNIQUE"}
 set_false_path -to [hdmi_cdc_pins $c D]
}
foreach relative {{source_release_reg\[[0-9]+\]} {csr_release_reg\[[0-9]+\]}} {
 set c [ai_mon_cells $relative 3]
 set clear [hdmi_cdc_pins $c CLR]
 if {[llength $c]!=3 || [llength $clear]!=3} {error "AI_MONITOR_RESET_CHAIN_CONTRACT"}
 set_false_path -to $clear
}
set ai_paths [get_timing_paths -from [hdmi_cdc_pins $ai_source C] -to [hdmi_cdc_pins $ai_capture D] -max_paths 1]
if {![llength $ai_paths]} {error "AI_MONITOR_BUS_PATH_CUT_OR_ABSENT"}
set ai_requirement [get_property REQUIREMENT [lindex $ai_paths 0]]
if {abs($ai_requirement-10.000)>0.001} {error "AI_MONITOR_BUS_BOUND_WRONG $ai_requirement"}
puts "AI_MONITOR_STABLE_BUS_ACTIVE source_bits=[llength $ai_source] capture_bits=[llength $ai_capture] max_ns=$ai_requirement source_period=$ai_source_period capture_period=$ai_capture_period"
