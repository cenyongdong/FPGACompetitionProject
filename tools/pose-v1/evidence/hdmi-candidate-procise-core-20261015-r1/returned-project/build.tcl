set root [pwd]
if {[catch {
 create_project -name candidate_core -device JFMQL30TAI676H
 add_design_file -file hdmi_axi_read.v hdmi_command_mailbox.v hdmi_scan_control.v hdmi_candidate_core.v hdmi_register_bank.v hdmi_candidate_register_core.v
 set_top -top hdmi_candidate_register_core
 save_project
 load_design -stage_elaborate -no_hier
 launch_run -stage synthesis
} r]} {puts "CANDIDATE_NATIVE_FAIL $r";exit 1}
puts "CANDIDATE_NATIVE_SYNTHESIS_RETURNED"
exit
