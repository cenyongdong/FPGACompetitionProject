# Read actual post-route paths, without changing their constraints.
set pf [open $protocol_validation_file w]
set pr {^U0_ps_ai_peripheral/hp2_protocol_recorder/}
set pb [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hp2_protocol_recorder/* && REF_NAME =~ RAMB*}]
set nc [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hp2_protocol_observer/native_checker/* && IS_PRIMITIVE}]
puts $pf "PROTOCOL_BRAM\t[llength $pb]"
puts $pf "PROTOCOL_NATIVE_PRIMITIVES\t[llength $nc]"
if {![llength $pb] || ![llength $nc]} {error "Native protocol checker or capture missing"}
foreach kind {META HELD RAW PSRESET} period {5 10 5 5} {
 set from {}
 if {$kind eq "META"} {
  set cells [get_cells -hier -regexp [format {%s(status_meta_reg\[[0-9]+\]|any_meta_reg)$} $pr]]
  set ends [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
 } elseif {$kind eq "HELD"} {
  set cells [get_cells -hier -regexp [format {%s(descriptor|first_status|any_status_held|any_cycle_held)_reg\[[0-9]+\]$} $pr]]
  set ends [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
  set src [get_cells -hier -regexp [format {%s(first_error/(trigger_cycle|trigger_index|valid_count|start_address)|first_pc_status|any_pc_status|any_cycle)_reg\[[0-9]+\]$} $pr]]
  set from [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
 } elseif {$kind eq "RAW"} {
  set ends {}
  foreach spec {{hp2_cycle_recorder 475 506} {hp2_protocol_recorder 354 385}} {
   lassign $spec instance lower upper
   foreach c [get_cells -quiet -hier -regexp [format {^U0_ps_ai_peripheral/%s/sample_stage_reg\[[0-9]+\]$} $instance]] {
    regexp {\[([0-9]+)\]$} [get_property NAME $c] unused bit
    if {$bit>=$lower && $bit<=$upper} {lappend ends [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
   }
  }
 } else {
  set from [get_pins -hier -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
  set ends [filter [all_fanout -flat -endpoints_only -from $from] {NAME =~ U0_ps_ai_peripheral/hp2_protocol_observer/* && REF_PIN_NAME == D}]
 }
 if {![llength $ends]} {error "Protocol $kind endpoints missing"}
 if {[llength $from]} {set p [get_timing_paths -from $from -to $ends -max_paths 1]} else {set p [get_timing_paths -to $ends -max_paths 1]}
 if {![llength $p]} {error "Protocol $kind paths absent/cut"}
 puts $pf "PROTOCOL_$kind\t[llength $ends]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {abs([get_property REQUIREMENT $p]-$period)>0.001 || [get_property SLACK $p]<0} {error "Protocol $kind timing failed"}
}
close $pf
