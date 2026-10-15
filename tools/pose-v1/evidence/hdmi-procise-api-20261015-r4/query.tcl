foreach c {export_sim_libs read_unimacro_lib compile_simlib_vlg} {if {[catch {$c -help} r]} {puts "HELP_ERROR $c $r"} else {puts "HELP_RESULT $c $r"}}
exit
