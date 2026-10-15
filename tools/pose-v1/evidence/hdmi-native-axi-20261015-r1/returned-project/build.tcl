
if {[catch {
create_project -name generated_axi -device JFMQL30TAI676H
add_design_file -file axi_infrastructure_v1_1_vl_rfs.v generic_baseblocks_v2_1_vl_rfs.v axi_crossbar_v2_1_vl_rfs.v axi_register_slice_v2_1_vl_rfs.v axi_data_fifo_v2_1_vl_rfs.v ps_ai_xbar_7.v ps_ai_s00_regslice_7.v ps_ai_s01_regslice_0.v ps_ai_m00_regslice_0.v ps_ai.v
set_top -top ps_ai_axi_interconnect_3_0
save_project
load_design -stage_elaborate -no_hier
launch_run -stage synthesis
} result]} {puts "NATIVE_AXI_FAIL $result";exit 1}
puts "NATIVE_AXI_SYNTHESIS_RETURNED"
exit
