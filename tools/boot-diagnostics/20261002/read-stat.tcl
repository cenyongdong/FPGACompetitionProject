get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number 210512180081} result]} { puts "SCAN_FAIL $result"; exit 1 }
if {[catch {read_reg -part 0 -reg STAT -read} result]} { puts "STAT_FAIL $result"; exit 1 }
puts "STAT_READ_COMPLETED $result"
exit