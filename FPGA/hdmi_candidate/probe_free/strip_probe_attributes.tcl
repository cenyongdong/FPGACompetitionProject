# The factory-linked functional checkpoint also carries MARK_DEBUG metadata.
# Remove those attributes without altering functional nets or timing exceptions.
set remaining_debug_cores [get_debug_cores -quiet]
if {[llength $remaining_debug_cores]} {error "Unexpected inherited debug core requires inspection: $remaining_debug_cores"}
set probe_marks [get_nets -quiet -hier -filter {MARK_DEBUG == 1}]
puts "REMOVED_FACTORY_MARK_DEBUG_COUNT [llength $probe_marks]"
foreach net $probe_marks {puts "REMOVED_FACTORY_MARK_DEBUG $net"}
if {[llength $probe_marks]} {set_property MARK_DEBUG false $probe_marks}
