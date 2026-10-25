# The constraints are already present. This reads physical paths only.
set trace_root {^U0_ps_ai_peripheral/hp2_cycle_recorder/}
# Callers may redirect the output using trace_validation_file.
if {![info exists trace_validation_file]} {set trace_validation_file hp2-cycletrace-native-facts.tsv}
set trace_f [open $trace_validation_file w]
set trace_ram [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hp2_cycle_recorder/* && REF_NAME =~ RAMB*}]
puts $trace_f "TRACE_BRAM\t[llength $trace_ram]"
if {![llength $trace_ram]} {error "Trace did not infer actual block RAM"}
foreach kind {META DESC RAW} period {5 10 5} {
 if {$kind eq "META"} {
  set cells [get_cells -hier -regexp [format {%sstatus_meta_reg\[[0-9]+\]$} $trace_root]]
 } elseif {$kind eq "DESC"} {
  set cells [get_cells -hier -regexp [format {%sdescriptor[01]_reg\[[0-9]+\]$} $trace_root]]
 } else {
  set cells {}
  foreach spec {{hp2_cycle_recorder 475 506} {hp2_protocol_recorder 354 385}} {
   lassign $spec instance lower upper
   foreach c [get_cells -quiet -hier -regexp [format {^U0_ps_ai_peripheral/%s/sample_stage_reg\[[0-9]+\]$} $instance]] {
    regexp {\[([0-9]+)\]$} [get_property NAME $c] unused bit
    if {$bit>=$lower && $bit<=$upper} {lappend cells $c}
   }
  }
 }
 set ends [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
 if {$kind eq "DESC"} {
  set sources [get_cells -hier -regexp [format {%s(first_return|pl_release)/(trigger_cycle|trigger_index|valid_count|start_address)_reg\[[0-9]+\]$} $trace_root]]
  set clocks [get_pins -of_objects $sources -filter {REF_PIN_NAME == C}]
  set p [get_timing_paths -from $clocks -to $ends -max_paths 1]
 } else {
  set p [get_timing_paths -to $ends -max_paths 1]
 }
 if {![llength $ends] || ![llength $p]} {error "Trace $kind paths missing/cut"}
 puts $trace_f "TRACE_$kind\t[llength $ends]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {abs([get_property REQUIREMENT $p]-$period)>0.001 || [get_property SLACK $p]<0} {error "Trace $kind timing failed"}
}
foreach cell $trace_ram {puts $trace_f "TRACE_RAM_CELL\t$cell\t[get_property REF_NAME $cell]"}
close $trace_f
