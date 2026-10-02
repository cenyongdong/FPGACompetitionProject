get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number 210512180081} result]} {
 puts "CHAIN_SCAN_FAIL $result"
 exit 1
}
puts "CHAIN_SCAN_COMPLETED"
exit