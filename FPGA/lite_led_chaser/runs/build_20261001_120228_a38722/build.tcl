# Run in a fresh, ASCII-only build directory containing the staged RTL/FDC.
if {[catch {
    create_project -name lite_led_chaser -device JFMQL30TAI676H
    add_design_file -file lite_led_chaser.v lite_led_chaser.fdc
    set_top -top lite_led_chaser
    save_project
    load_design -stage_elaborate -no_hier
    launch_run -stage bitstream
    # launch_run uses default Cclk. Explicitly regenerate for JTAG startup.
    # Approved by the user on 2026-10-01; no Flash image is generated.
    bitgen lite_led_chaser.bit -g StartupClk:JtagClk
} result]} {
    puts "BUILD_TCL_FAIL $result"
    exit 1
}
puts "BUILD_TCL_COMPLETED"
exit
