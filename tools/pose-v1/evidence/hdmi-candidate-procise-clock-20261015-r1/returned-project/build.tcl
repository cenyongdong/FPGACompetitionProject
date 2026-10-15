set root [pwd]
if {[catch {
 create_project -name candidate_clock -device JFMQL30TAI676H
 add_design_file -file hdmi_clock_fmsh.v
 set_top -top hdmi_clock_fmsh
 save_project
 load_design -stage_elaborate -no_hier
 launch_run -stage synthesis
} r]} {puts "CANDIDATE_NATIVE_FAIL $r";exit 1}
puts "CANDIDATE_NATIVE_SYNTHESIS_RETURNED"
exit
