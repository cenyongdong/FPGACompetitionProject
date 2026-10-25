# Run on the actual complete physical checkpoint. No constraints are added here.
set dcroot {^U0_ps_ai_peripheral/deferred_control/}
set dcf [open $deferred_validation_file w]
foreach kind {TOGGLE REPLY COMMAND} expected {5 10 5} {
 if {$kind eq "TOGGLE"} {
  set cells [get_cells -hier -regexp [format {%s(request_sync|ack_sync)_reg\[0\]$} $dcroot]]
  set ends [get_pins -of_objects $cells -filter {REF_PIN_NAME == D}]
  set paths [get_timing_paths -to $ends -max_paths 1]
 } elseif {$kind eq "REPLY"} {
  set src [get_cells -hier -regexp [format {%sheld_(status|pc|cycle|arm_cycle|flags)_reg\[[0-9]+\]$} $dcroot]]
  set dst [get_cells -hier -regexp [format {%scsr_(status|pc|cycle|arm_cycle|flags)_reg\[[0-9]+\]$} $dcroot]]
  set ends [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
  set paths [get_timing_paths -from [get_pins -of_objects $src -filter {REF_PIN_NAME == C}] -to $ends -max_paths 1]
 } else {
  set src [get_cells -hier -regexp [format {%sheld_command_reg\[[0-9]+\]$} $dcroot]]
  set ends [filter [all_fanout -flat -endpoints_only -from [get_pins -of_objects $src -filter {REF_PIN_NAME == Q}]] {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
  set paths [get_timing_paths -from [get_pins -of_objects $src -filter {REF_PIN_NAME == C}] -to $ends -max_paths 1]
 }
 if {![llength $ends] || ![llength $paths]} {error "Deferred $kind paths missing or cut"}
 set p [lindex $paths 0];set r [get_property REQUIREMENT $p];set slack [get_property SLACK $p]
 puts $dcf "$kind\t[llength $ends]\t$r\t$slack"
 if {![string is double -strict $r] || abs($r-$expected)>0.001} {error "Deferred $kind actual bound absent/cut"}
 if {![info exists deferred_unplaced_coverage_only] && $slack<0} {error "Deferred $kind final slack failed"}
 if {![info exists deferred_unplaced_coverage_only]} {
  # Prove every endpoint remains timed; a single worst path can miss a cut bit.
  foreach endpoint $ends {
   if {$kind eq "TOGGLE"} {
    set single [get_timing_paths -to $endpoint -max_paths 1]
   } else {
    set single [get_timing_paths -from [get_pins -of_objects $src -filter {REF_PIN_NAME == C}] -to $endpoint -max_paths 1]
   }
   if {![llength $single]} {error "Deferred $kind endpoint missing or cut: $endpoint"}
   set er [get_property REQUIREMENT $single];set es [get_property SLACK $single]
   puts $dcf "${kind}_ENDPOINT\t$endpoint\t$er\t$es"
   if {![string is double -strict $er] || abs($er-$expected)>0.001 || $es<0} {error "Deferred $kind endpoint fails its actual bound: $endpoint"}
  }
 }
}
close $dcf
