"""Preserve the qualified factory PS implementation, expose one unused output."""
from prepare_ps_release_candidate import REF,W,E,wrap
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=2);args=parser.parse_args()
old=REF/'fpai_demo_vivado.srcs/sources_1/bd/ps_ai/ip/ps_ai_processing_system7_0_0/ps_ai_processing_system7_0_0.dcp'
t='open_checkpoint {'+old.as_posix()+'}\n'
t+=r'''
set ps [get_cells -hier -filter {REF_NAME == PS7}]
if {[llength $ps]!=1} {error "Factory PS primitive missing"}
set pin [get_pins -of_objects $ps -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
if {[llength $pin]!=1 || [llength [get_ports -quiet S_AXI_HP2_ARESETN]]} {error "Unexpected original PS port contract"}
set f [open {@@E@@/factory-PS-export-facts.tsv} w]
puts $f "BASE_CHECKPOINT\t@@OLD@@"
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
write_checkpoint -force {@@W@@/ps-export.dcp}
'''
t=t.replace('@@E@@',E.as_posix()).replace('@@W@@',W.as_posix()).replace('@@OLD@@',old.as_posix())
t=t.replace('factory-PS-export-facts.tsv','factory-PS-export-facts-r'+str(args.attempt)+'.tsv')
(E/('ps-export-r'+str(args.attempt)+'.tcl')).write_text(wrap(t))
