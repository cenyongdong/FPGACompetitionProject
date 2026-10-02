# Approved independent xlconcat source-bridge experiment (2026-10-01).
# No Xilinx DCP, simulation-only model, stub, or Vivado synthesis is imported.
set build_root [pwd]
if {[catch {
    create_project -name lite_led_chaser -device JFMQL30TAI676H
    add_design_file -file xlconcat_v2_1_vl_rfs.v led_state_concat.v lite_led_chaser.v lite_led_chaser.fdc
    set_top -top lite_led_chaser
    save_project
    load_design -stage_elaborate -no_hier
    launch_run -stage bitstream
    cd [file join $build_root rundir]
    bitgen lite_led_chaser.bit -g StartupClk:JtagClk
} result]} {
    puts "BUILD_TCL_FAIL $result"
    exit 1
}
puts "BUILD_TCL_COMPLETED"
exit
