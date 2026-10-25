# Passive release recorder: bounded transfers, no new false path or clock cut.
set root {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/}
set src [get_cells -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $root]]
set dst [get_cells -hier -regexp [format {%scsr_source_snapshot_reg\[[0-9]+\]$} $root]]
if {![llength $src] || [llength $src]!=[llength $dst]} {error "PS_RELEASE_HELD_BUS_MISSING"}
set srcC [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
set dstD [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
set_max_delay -datapath_only 10.000 -from $srcC -to $dstD
set meta [get_cells -hier -regexp [format {%s(levels_meta_reg\[[0-9]+\]|beat_meta_reg)$} $root]]
# Bit7 is a reserved constant input; the sampled bit7 is the independent
# heartbeat witness. ASYNC_REG can retain the unused constant register pre-opt.
set dynamic_meta {}
foreach c $meta {if {![regexp {levels_meta_reg\[7\]$} [get_property NAME $c]]} {lappend dynamic_meta $c}}
set meta $dynamic_meta
if {[llength $meta]<16} {error "PS_RELEASE_SYNCHRONIZERS_MISSING"}
set metaD [get_pins -of_objects $meta -filter {REF_PIN_NAME == D}]
# Narrow the existing factory sys_rst aggregate cut: retain every old endpoint
# and every asynchronous clear; remove only the new recorder's data inputs.
set key [get_ports sys_rst]
set key_ends [all_fanout -flat -endpoints_only -from $key]
set key_old {};set key_new_data {}
foreach p $key_ends {
 if {([string match U0_ps_ai_peripheral/ai_read_path_monitor/release_history/* [get_property NAME $p]] || [string match U0_ps_ai_peripheral/hp2_cycle_recorder/* [get_property NAME $p]] || [string match U0_ps_ai_peripheral/hp2_protocol_recorder/* [get_property NAME $p]] || [string match U0_ps_ai_peripheral/hp2_protocol_observer/* [get_property NAME $p]]) && [get_property REF_PIN_NAME $p] eq "D"} {
  lappend key_new_data $p
 } else {lappend key_old $p}
}
if {![llength $key_new_data] || ![llength $key_old]} {error "PS_RELEASE_RESET_DATA_SCOPE_MISSING"}
set_max_delay -reset_path -datapath_only 5.000 -from $key
set_false_path -from $key -through $key_old
set_max_delay -datapath_only 5.000 -from $key -to $key_new_data
set starts [all_fanin -flat -startpoints_only -to $metaD]
set_max_delay -datapath_only 5.000 -from $starts -to $metaD
set paths [get_timing_paths -from $srcC -to $dstD -max_paths 1]
if {![llength $paths] || abs([get_property REQUIREMENT $paths]-10)>0.001} {error "PS_RELEASE_HELD_BUS_CUT"}
foreach pin $metaD {
 set paths [get_timing_paths -to $pin -max_paths 1]
 if {![llength $paths] || [get_property REQUIREMENT $paths] eq "" || abs([get_property REQUIREMENT $paths]-5)>0.001} {error "PS_RELEASE_SYNC_PATH_CUT $pin"}
}
set ps [get_pins -hier -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
if {[llength $ps]!=1} {error "PS_RELEASE_REAL_PS_OUTPUT_MISSING"}
set endpoints [all_fanout -flat -endpoints_only -from $ps]
if {![llength [filter $endpoints {NAME =~ *ai_read_path_monitor/release_history/*}]]} {error "PS_RELEASE_REAL_OUTPUT_NOT_CONNECTED"}
puts "PS_RELEASE_BOUND held_bits=[llength $src] first_stage_bits=[llength $meta] PS_output=$ps"
