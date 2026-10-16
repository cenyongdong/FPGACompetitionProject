catch {create_boot_image -help} m
puts "CREATE_HELP_RESULT $m"
catch {dump_boot_image -help} m
puts "DUMP_HELP_RESULT $m"
puts "HELP_COMPLETE"
exit
