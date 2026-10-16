
puts "INCREMENT_COMMAND [info commands increment_bit_cfg_v3]"
puts "BOOT_COMMANDS [info commands *boot*]"
puts "IMAGE_COMMANDS [info commands *image*]"
if {[llength [info commands increment_bit_cfg_v3]]} {
 if {[catch {help increment_bit_cfg_v3} r]} {puts "HELP_EXCEPTION $r"} else {puts "HELP_RETURN $r"}
}
puts "COMMAND_REVIEW_COMPLETE_NO_BIT_INPUT"
exit
