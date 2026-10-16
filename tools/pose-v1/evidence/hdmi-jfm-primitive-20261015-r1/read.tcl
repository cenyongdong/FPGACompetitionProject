
if {[catch {
 create_project -in_memory -part xc7z030ffg676-2
 puts "LOCAL_030AI_DECLARATION_READ_BEGIN"
 read_verilog -library fmsh030ai unisim_comp.v
 puts "LOCAL_030AI_DECLARATION_READ_COMPLETE"
 synth_design -rtl -top PS7 -part xc7z030ffg676-2
 set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-jfm-primitive-20261015-r1/PS7-ports.txt} w]
 foreach port [get_ports] {puts $f "$port|[get_property DIRECTION $port]"}
 close $f
 close_design
 close_project
 puts "LOCAL_030AI_DECLARATION_PORTS_READ_COMPLETE"
} result]} {puts "LOCAL_030AI_DECLARATION_READ_FAIL $result";exit 1}
exit
