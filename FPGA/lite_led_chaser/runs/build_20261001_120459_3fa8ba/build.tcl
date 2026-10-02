# Run in a fresh, ASCII-only build directory containing the staged RTL/FDC.
set build_root [pwd]
if {[catch {
    create_project -name lite_led_chaser -device JFMQL30TAI676H
    add_design_file -file lite_led_chaser.v lite_led_chaser.fdc
    set_top -top lite_led_chaser
    save_project
    load_design -stage_elaborate -no_hier
    launch_run -stage bitstream
    # launch_run uses default Cclk. Explicitly regenerate for JTAG startup.
    # Approved by the user on 2026-10-01; no Flash image is generated.
    # launch_run returns to the project root; explicitly select the artifact dir.
    cd [file join $build_root rundir]
    bitgen lite_led_chaser.bit -g StartupClk:JtagClk
} result]} {
    puts "BUILD_TCL_FAIL $result"
    exit 1
}
puts "BUILD_TCL_COMPLETED"
exit
