puts "PREFLIGHT Tcl [info patchlevel]"
puts "CHAIN_COMMANDS [info commands *chain*]"
puts "CABLE_COMMANDS [info commands *cable*]"
puts "JTAG_COMMANDS [info commands *jtag*]"
puts "PROGRAM_COMMANDS [info commands *program*]"
foreach cmd {init_chain program_bit} {
    puts "HELP $cmd"
    if {[catch {help $cmd} result]} {puts "HELP_QUERY_ERROR $result"} else {puts $result}
}
exit