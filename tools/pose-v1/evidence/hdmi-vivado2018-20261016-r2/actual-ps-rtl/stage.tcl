
if {[catch {
 if {[version -short] ne "2018.3"} {error "Wrong Vivado version"}
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog [list ps_ai_processing_system7_0_0.v processing_system7_v5_5_processing_system7.v processing_system7_v5_5_atc.v processing_system7_v5_5_aw_atc.v processing_system7_v5_5_b_atc.v processing_system7_v5_5_trace_buffer.v processing_system7_v5_5_w_atc.v]
 synth_design -rtl -top ps_ai_processing_system7_0_0 -part xc7z030ffg676-2
 
 set cells [get_cells -hierarchical -filter {REF_NAME == PS7}]
 if {[llength $cells]!=1} {error "Expected one actual PS7 primitive"}
 puts "ACTUAL_PS7_PRIMITIVE $cells"
 report_property $cells
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/actual-ps-rtl/actual-PS7-pins.txt} w]
 foreach pin [get_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 set lib [get_lib_cells PS7]
 report_property $lib
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/actual-ps-rtl/library-PS7-pins.txt} w]
 foreach pin [get_lib_pins -of_objects $lib] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f

 puts "ACTUAL_EXTENDED_PS_GATE_COMPLETE"
 close_design
 close_project
} result]} {puts "ACTUAL_EXTENDED_PS_GATE_FAILED $result";exit 1}
exit
