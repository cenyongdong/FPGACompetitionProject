if {[catch {
set_param general.maxThreads 2
open_checkpoint {D:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ip/ps_ai_processing_system7_0_0/ps_ai_processing_system7_0_0.dcp}

set ps [get_cells -hier -filter {REF_NAME == PS7}]
if {[llength $ps]!=1} {error "Factory PS primitive missing"}
set pin [get_pins -of_objects $ps -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
if {[llength $pin]!=1 || [llength [get_ports -quiet S_AXI_HP2_ARESETN]]} {error "Unexpected original PS port contract"}
set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/factory-PS-export-facts-r2.tsv} w]
puts $f "BASE_CHECKPOINT\tD:/FPGACompetitionProject/.local/hdmi-boot-witness-20261019-r23/reference/fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ip/ps_ai_processing_system7_0_0/ps_ai_processing_system7_0_0.dcp"
puts $f "BASE_CELLS\t[llength [get_cells -hier]]"
puts $f "BASE_PORTS\t[llength [get_ports]]"
foreach c [get_cells -hier -filter {REF_NAME == OBUFT}] {
 puts $f "IOBUF\t$c\t[get_nets -of_objects [get_pins $c/I]]"
}
create_port -direction OUT S_AXI_HP2_ARESETN
set net [get_nets -quiet -of_objects $pin]
if {![llength $net]} {
 create_net ps_release_hp2_resetn;set net [get_nets ps_release_hp2_resetn]
 connect_net -hierarchical -net $net -objects $pin
}
connect_net -hierarchical -net $net -objects [get_ports S_AXI_HP2_ARESETN]
puts $f "NEW_CELLS\t[llength [get_cells -hier]]"
puts $f "NEW_PORTS\t[llength [get_ports]]"
puts $f "NEW_OUTPUT\t$pin\t[get_nets -segments -of_objects $pin]"
close $f
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/ps-export.dcp}

} result]} {puts $result;puts $::errorInfo;exit 1}
exit
