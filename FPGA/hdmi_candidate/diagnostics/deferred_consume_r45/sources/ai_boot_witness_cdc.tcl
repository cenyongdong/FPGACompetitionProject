# Bounded CDC for passive boot history. No additional cut/clock waiver.
# The existing hdmi_cdc.tcl scopes the factory HP->GP cut by legacy launch
# pins. These five observed reset/calibration signals originate on legacy
# pins, so that cut also covered the new first-stage D pins. Replace the
# exact old aggregate cut by its intersection with legacy capture inputs.
# Keeping the original FROM and TO and adding THROUGH can only remove cuts.
set boot_gp_clock [get_clocks clk_out1_clk_wiz_0]
set boot_hp_clock [get_clocks clk_pll_i]
set boot_legacy_launch [filter [all_registers -clock $boot_hp_clock -clock_pins] {NAME !~ U0_ps_ai_peripheral/hdmi_display/* && NAME !~ U0_ps_ai_peripheral/ai_path_monitor/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/* && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_observer/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set boot_legacy_capture [filter [all_registers -clock $boot_gp_clock -cells] {NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/boot_history*witness/* && NAME !~ U0_ps_ai_peripheral/ai_read_path_monitor/release_history/* && NAME !~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && NAME !~ U0_ps_ai_peripheral/hp2_protocol_observer/* && NAME !~ U0_ps_ai_peripheral/deferred_control/* && NAME !~ U0_ps_ai_peripheral/startup_drain/*}]
set boot_legacy_inputs [get_pins -of_objects $boot_legacy_capture -filter {DIRECTION == IN && IS_CLOCK == 0}]
if {[llength $boot_gp_clock]!=1 || [llength $boot_hp_clock]!=1 || ![llength $boot_legacy_launch] || ![llength $boot_legacy_inputs]} {
 error "BOOT_WITNESS_FACTORY_SCOPE_MISSING"
}
set_max_delay -reset_path -datapath_only 10.000 -from $boot_legacy_launch -to $boot_gp_clock
set_false_path -from $boot_legacy_launch -to $boot_gp_clock -through $boot_legacy_inputs
set boot_root {^U0_ps_ai_peripheral/ai_read_path_monitor/boot_history[./]witness/}
set boot_source [get_cells -quiet -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $boot_root]]
set boot_capture_all [get_cells -quiet -hier -regexp [format {%scsr_snapshot_reg\[[0-9]+\]$} $boot_root]]
set boot_capture {};set boot_source_indices {};set boot_capture_indices {}
foreach cell $boot_source {
 regexp {\[([0-9]+)\]$} [get_property NAME $cell] unused index
 lappend boot_source_indices $index
}
foreach cell $boot_capture_all {
 regexp {\[([0-9]+)\]$} [get_property NAME $cell] unused index
 if {$index<384} {lappend boot_capture $cell;lappend boot_capture_indices $index}
}
if {[llength $boot_source]<128 ||
    [lsort -integer -unique $boot_source_indices] ne [lsort -integer -unique $boot_capture_indices]} {
 error "BOOT_WITNESS_STABLE_BUS_MISSING_OR_MISMATCHED source=[llength $boot_source] capture=[llength $boot_capture]"
}
set boot_source_C [get_pins -of_objects $boot_source -filter {REF_PIN_NAME == C}]
set boot_capture_D [get_pins -of_objects $boot_capture -filter {REF_PIN_NAME == D}]
set_max_delay -datapath_only 10.000 -from $boot_source_C -to $boot_capture_D
set boot_meta [get_cells -quiet -hier -regexp [format {%sflags_meta_reg\[[0-9]+\]$} $boot_root]]
if {![llength $boot_meta]} {error "BOOT_WITNESS_GP_FLAG_SYNCHRONIZER_MISSING"}
set boot_meta_D [get_pins -of_objects $boot_meta -filter {REF_PIN_NAME == D}]
set boot_flag_sources [all_fanin -flat -startpoints_only -to $boot_meta_D]
if {![llength $boot_flag_sources]} {error "BOOT_WITNESS_FLAG_STARTPOINTS_MISSING"}
set_max_delay -datapath_only 5.000 -from $boot_flag_sources -to $boot_meta_D
set boot_flag_paths [get_timing_paths -to $boot_meta_D -max_paths [llength $boot_meta_D] -nworst 1]
if {[llength $boot_flag_paths]!=[llength $boot_meta_D]} {error "BOOT_WITNESS_FLAG_PATHS_MISSING"}
foreach path $boot_flag_paths {
 set requirement [get_property REQUIREMENT $path]
 if {$requirement eq "" || abs($requirement-5.000)>0.001} {error "BOOT_WITNESS_FLAG_BOUND_CUT_OR_WRONG"}
}
set boot_paths [get_timing_paths -from $boot_source_C -to $boot_capture_D -max_paths 1]
if {![llength $boot_paths] || abs([get_property REQUIREMENT [lindex $boot_paths 0]]-10.000)>0.001} {
 error "BOOT_WITNESS_STABLE_BUS_UNCONSTRAINED_OR_CUT"
}
puts "BOOT_WITNESS_CDC_BOUND source_bits=[llength $boot_source] capture_bits=[llength $boot_capture] max_ns=10 GP_flags_max_ns=5"
