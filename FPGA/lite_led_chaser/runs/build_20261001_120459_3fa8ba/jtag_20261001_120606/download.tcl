get_cable_info
if {[catch {init_chain -cable_type usb-jtag-hs1 -serial_number 210512180081} result]} {
    puts "PROGRAM_CHAIN_FAIL $result"
    exit 1
}
puts "PROGRAM_EXPECTED_TARGET jfmql30 part 0 IDCODE 0x9372c093"
if {[catch {program_bit {D:/FPGACompetitionProject/FPGA/lite_led_chaser/runs/build_20261001_120459_3fa8ba/rundir/lite_led_chaser.bit} -part 0} result]} {
    puts "PROGRAM_TCL_FAIL $result"
    exit 1
}
puts "PROGRAM_TCL_COMPLETED"
if {[catch {read_reg -part 0 -reg STAT -read} result]} {
    puts "STATUS_READ_UNAVAILABLE $result"
} else {
    puts "STATUS_READ_RESULT $result"
}
exit