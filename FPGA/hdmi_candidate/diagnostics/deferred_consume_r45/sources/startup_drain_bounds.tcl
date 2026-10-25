# Bound the newly consumed raw PS reset output, as for the existing observer.
# This adds coverage at one HP period; it adds no false path or clock exception.
set drain_psn [get_pins -hier -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
if {[llength $drain_psn]!=1} {error "PS HP2 reset output missing"}
set drain_psn_ends [filter [all_fanout -flat -endpoints_only -from $drain_psn] {REF_PIN_NAME == D || REF_PIN_NAME == CE}]
if {![llength $drain_psn_ends]} {error "PS reset consumer endpoints missing"}
set_max_delay -datapath_only 5.000 -from $drain_psn -to $drain_psn_ends
puts "BOUNDED_DRAIN_RAW_RESET_BOUND [llength $drain_psn_ends] endpoints 5ns"
