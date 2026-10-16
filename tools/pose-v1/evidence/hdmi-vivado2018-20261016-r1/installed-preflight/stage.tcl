
if {[catch {
 puts "INSTALLED_VERSION [version -short]"
 puts "INSTALLED_ROOT $::env(XILINX_VIVADO)"
 if {[version -short] ne "2018.3"} {error "Unexpected installed Vivado version"}
 set f [open anchor.v w]
 puts $f {module metadata_anchor(input a, output y); assign y=a; endmodule}
 close $f
 create_project -in_memory -part xc7z030ffg676-2
 read_verilog anchor.v
 synth_design -rtl -top metadata_anchor -part xc7z030ffg676-2
 set cells [get_lib_cells -quiet *PS7*]
 if {[llength $cells]!=1} {error "Expected one PS7 library cell"}
 report_property $cells
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-vivado2018-20261016-r1/installed-preflight/builtin-PS7-pins.txt} w]
 foreach pin [get_lib_pins -of_objects $cells] {puts $f "$pin|[get_property DIRECTION $pin]"}
 close $f
 close_design
 close_project
 puts "INSTALLED_PREFLIGHT_COMPLETE"
} result]} {puts "INSTALLED_PREFLIGHT_FAIL $result";exit 1}
exit
