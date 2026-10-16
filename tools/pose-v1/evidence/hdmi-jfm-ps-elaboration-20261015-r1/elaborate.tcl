
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog -library fmsh030ai unisim_comp.v
 read_verilog [list processing_system7_v5_5_atc.v processing_system7_v5_5_aw_atc.v processing_system7_v5_5_b_atc.v processing_system7_v5_5_processing_system7.v processing_system7_v5_5_trace_buffer.v processing_system7_v5_5_w_atc.v ps_ai_processing_system7_0_0.v]
 puts "LOCAL_PS_RTL_ELABORATION_BEGIN"
 synth_design -rtl -top ps_ai_processing_system7_0_0 -part xc7z030ffg676-2
 set cells [get_cells -hierarchical -filter {REF_NAME == PS7}]
 puts "LOCAL_PS7_CELL_COUNT [llength $cells]"
 if {[llength $cells]!=1} {error "Expected one real PS7 declaration binding"}
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-ps-elaboration-20261015-r1/PS7-pins.txt} w]
 foreach pin [get_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 report_property $cells
 close_design
 close_project
 puts "LOCAL_PS_RTL_ELABORATION_METADATA_COMPLETE"
} result]} {puts "LOCAL_PS_RTL_ELABORATION_FAIL $result";exit 1}
exit
