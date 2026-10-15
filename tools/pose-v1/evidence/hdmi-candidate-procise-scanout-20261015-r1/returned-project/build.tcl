set root [pwd]
if {[catch {
 create_project -name candidate_scanout -device JFMQL30TAI676H
 add_design_file -file hdmi_axi_read.v hdmi_command_mailbox.v hdmi_scan_control.v hdmi_candidate_core.v hdmi_register_bank.v hdmi_candidate_register_core.v hdmi_stream_fifo.v hdmi_pixel_scan.v hdmi_scanout.v
 set_top -top hdmi_scanout
 save_project
 load_design -stage_elaborate -no_hier
 launch_run -stage synthesis
} r]} {puts "CANDIDATE_NATIVE_FAIL $r";exit 1}
puts "CANDIDATE_NATIVE_SYNTHESIS_RETURNED"
exit
