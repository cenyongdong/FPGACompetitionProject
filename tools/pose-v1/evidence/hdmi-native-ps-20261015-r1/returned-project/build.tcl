
if {[catch {
create_project -name generated_axi -device JFMQL30TAI676H
add_design_file -file ps_ai_processing_system7_0_0.v processing_system7_v5_5_processing_system7.v processing_system7_v5_5_atc.v processing_system7_v5_5_aw_atc.v processing_system7_v5_5_b_atc.v processing_system7_v5_5_trace_buffer.v processing_system7_v5_5_w_atc.v
set_top -top ps_ai_processing_system7_0_0
save_project
load_design -stage_elaborate -no_hier
launch_run -stage synthesis
} result]} {puts "NATIVE_AXI_FAIL $result";exit 1}
puts "NATIVE_AXI_SYNTHESIS_RETURNED"
exit
