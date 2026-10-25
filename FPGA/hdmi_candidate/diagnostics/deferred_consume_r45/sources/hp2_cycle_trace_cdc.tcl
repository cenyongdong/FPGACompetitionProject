# Passive trace: bound every newly added cross-domain data path. No clock cut
# or false path is added. The pre-existing reset aggregate excludes trace D.
set trace_root {^U0_ps_ai_peripheral/hp2_cycle_recorder/}
set trace_meta [get_cells -hier -regexp [format {%sstatus_meta_reg\[[0-9]+\]$} $trace_root]]
set trace_meta_D [get_pins -of_objects $trace_meta -filter {REF_PIN_NAME == D}]
if {[llength $trace_meta_D]!=4} {error "Trace status synchronizers missing"}
set trace_starts [all_fanin -flat -startpoints_only -to $trace_meta_D]
set_max_delay -datapath_only 5.000 -from $trace_starts -to $trace_meta_D
set trace_src [get_cells -hier -regexp [format {%s(first_return|pl_release)/(trigger_cycle|trigger_index|valid_count|start_address)_reg\[[0-9]+\]$} $trace_root]]
set trace_dst [get_cells -hier -regexp [format {%sdescriptor[01]_reg\[[0-9]+\]$} $trace_root]]
set trace_src_C [get_pins -of_objects $trace_src -filter {REF_PIN_NAME == C}]
set trace_dst_D [get_pins -of_objects $trace_dst -filter {REF_PIN_NAME == D}]
if {![llength $trace_src_C] || ![llength $trace_dst_D]} {error "Trace held descriptors missing"}
set_max_delay -datapath_only 10.000 -from $trace_src_C -to $trace_dst_D
set trace_raw_D {}
foreach spec {{hp2_cycle_recorder 475 506} {hp2_protocol_recorder 354 385}} {
 lassign $spec instance lower upper
 foreach c [get_cells -quiet -hier -regexp [format {^U0_ps_ai_peripheral/%s/sample_stage_reg\[[0-9]+\]$} $instance]] {
  regexp {\[([0-9]+)\]$} [get_property NAME $c] unused bit
  if {$bit>=$lower && $bit<=$upper} {lappend trace_raw_D [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
 }
}
if {![llength $trace_raw_D]} {error "Trace flag sample stage missing"}
set trace_starts [all_fanin -flat -startpoints_only -to $trace_raw_D]
set_max_delay -datapath_only 5.000 -from $trace_starts -to $trace_raw_D
puts "HP2_TRACE_BOUNDS status=[llength $trace_meta_D] descriptor=[llength $trace_dst_D] flags=[llength $trace_raw_D]"
