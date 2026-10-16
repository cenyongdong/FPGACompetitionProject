
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog anchor.v
 synth_design -rtl -top metadata_anchor -part xc7z030ffg676-2
 set cells [get_lib_cells -quiet *PS7*]
 puts "METADATA_PS7_LIBRARY_CELLS $cells"
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2019-library-20261015-r1/builtin-PS7-pins.txt} w]
 foreach cell $cells {
  puts $f "CELL|$cell"
  report_property $cell
  foreach pin [get_lib_pins -of_objects $cell] {
   puts $f "$pin|[get_property DIRECTION $pin]"
  }
 }
 close $f
 close_design
 close_project
 puts "METADATA_QUERY_FINISHED"
} result]} {puts "METADATA_QUERY_FAILED $result";exit 1}
exit
