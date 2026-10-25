# New observer only: no new clock cuts or false paths. All sampled reset/status
# inputs have explicit one-HP-period bounds; immutable buses have one GP period.
set pr {^U0_ps_ai_peripheral/hp2_protocol_recorder/}
set pm [get_cells -hier -regexp [format {%s(status_meta_reg\[[0-9]+\]|any_meta_reg)$} $pr]]
set pmD [get_pins -of_objects $pm -filter {REF_PIN_NAME == D}]
if {[llength $pmD]!=7} {error "Protocol status synchronizers missing"}
set_max_delay -datapath_only 5.000 -from [all_fanin -flat -startpoints_only -to $pmD] -to $pmD
set ph [get_cells -hier -regexp [format {%s(first_error/(trigger_cycle|trigger_index|valid_count|start_address)|first_pc_status|any_pc_status|any_cycle)_reg\[[0-9]+\]$} $pr]]
set pd [get_cells -hier -regexp [format {%s(descriptor|first_status|any_status_held|any_cycle_held)_reg\[[0-9]+\]$} $pr]]
set phC [get_pins -of_objects $ph -filter {REF_PIN_NAME == C}]
set pdD [get_pins -of_objects $pd -filter {REF_PIN_NAME == D}]
if {![llength $phC] || ![llength $pdD]} {error "Protocol held result bus missing"}
set_max_delay -datapath_only 10.000 -from $phC -to $pdD
set rawD {}
# Both recorders sample the same flags. Equivalent registers can merge into
# either hierarchy; retain the same one-HP-period bound in both cases.
foreach spec {{hp2_cycle_recorder 475 506} {hp2_protocol_recorder 354 385}} {
 lassign $spec instance lower upper
 foreach c [get_cells -quiet -hier -regexp [format {^U0_ps_ai_peripheral/%s/sample_stage_reg\[[0-9]+\]$} $instance]] {
  regexp {\[([0-9]+)\]$} [get_property NAME $c] unused bit
  if {$bit>=$lower && $bit<=$upper} {lappend rawD [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
 }
}
if {![llength $rawD]} {error "Protocol raw flags missing"}
set_max_delay -datapath_only 5.000 -from [all_fanin -flat -startpoints_only -to $rawD] -to $rawD
set psn [get_pins -hier -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
set pe [filter [all_fanout -flat -endpoints_only -from $psn] {NAME =~ U0_ps_ai_peripheral/hp2_protocol_observer/* && REF_PIN_NAME == D}]
if {[llength $psn]!=1 || ![llength $pe]} {error "Native checker PS reset observation missing"}
set_max_delay -datapath_only 5.000 -from $psn -to $pe
puts "HP2_PROTOCOL_BOUNDS meta=[llength $pmD] held=[llength $pdD] raw=[llength $rawD] ps_reset=[llength $pe]"
