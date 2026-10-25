# r45: exclusion is applied at initial creation in hdmi_cdc.tcl and
# ps_release_raw_flags_cdc.tcl, before any timing graph is queried.
# This only narrows inherited legacy cuts; it adds no new false path.
source [file join [file dirname [info script]] hp2_cycle_trace_cdc.tcl]
source [file join [file dirname [info script]] hp2_protocol_cdc.tcl]
foreach p [lsort -unique [concat $trace_meta_D $pmD $rawD $pe]] {
 set t [get_timing_paths -to $p -max_paths 1]
 set r [get_property REQUIREMENT $t]
 if {![string is double -strict $r] || abs($r-5)>0.001} {error "Diagnostic first-stage bound absent/cut: $p requirement=$r"}
}
puts "DIAGNOSTIC_EXCLUDED_FROM_INITIAL_LEGACY_CUTS actual_first_stage_bounds_checked"
