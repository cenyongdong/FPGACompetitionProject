puts "LIBRARY_QUERY_COMMANDS [info commands *lib*]"
puts "PROPERTY_QUERY_COMMANDS [info commands *property*]"
foreach c {get_lib_cells get_lib_pins read_lib list_library set_device} {if {[catch {help $c} r]} {puts "HELP_ERROR $c $r"} else {puts "HELP_RESULT $c $r"}}
exit
