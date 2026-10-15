set root [pwd]
if {[catch {
 create_project -name candidate_diff_route -device JFMQL30TAI676H
 add_design_file -file hdmi_diff_output_fmsh.v diff_output_compatibility.fdc
 set_top -top hdmi_diff_output_fmsh
 save_project
 load_design -stage_elaborate -no_hier
 launch_run -stage route
} r]} {puts "CANDIDATE_NATIVE_FAIL $r";exit 1}
puts "CANDIDATE_NATIVE_SYNTHESIS_RETURNED"
exit
