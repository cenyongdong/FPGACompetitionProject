
if {[catch {
 create_project -name imported_ps -device JFMQL30TAI676H
 add_design_file -file actual_ps.edf
 set_top -top ps_ai_processing_system7_0_0
 save_project
 load_design -stage_post_elaborate -no_hier
 puts "NATIVE_REAL_PS_EDIF_POST_ELABORATE_COMPLETE"
} result]} {puts "NATIVE_REAL_PS_EDIF_IMPORT_FAILED $result";exit 1}
exit
