"""Avoid a second PJTAG output buffer when loading the explicit PS stub."""
from prepare_ps_release_candidate import W,E,S
t=(E/'synthesis.tcl').read_text()
diagnostic=r'''
open_checkpoint {@@W@@/linked.dcp}
set f [open {@@E@@/pjtag-buffer-facts.tsv} w]
set n [get_nets -of_objects [get_ports PJTAG_TDO]]
foreach p [get_pins -leaf -of_objects $n -filter {DIRECTION == OUT}] {
 set c [get_cells -of_objects $p]
 puts $f "TOP_DRIVER\t$p\t[get_property REF_NAME $c]"
 foreach q [get_pins -leaf -of_objects [get_nets -of_objects [get_pins $c/I]] -filter {DIRECTION == OUT}] {
  puts $f "UPSTREAM_DRIVER\t$q\t[get_property REF_NAME [get_cells -of_objects $q]]"
 }
}
close $f
close_project
'''.replace('@@W@@',W.as_posix()).replace('@@E@@',E.as_posix())
t=t.replace('set_param general.maxThreads 2\n','set_param general.maxThreads 2\n'+diagnostic,1)
xdc=S/'ps-managed-io.xdc'
xdc.write_text('# PJTAG already has the qualified OBUFT inside the PS OOC.\nset_property IO_BUFFER_TYPE NONE [get_ports PJTAG_TDO]\n')
t=t.replace('synth_design -top ai7030_edif_top',
            'read_xdc {'+xdc.as_posix()+'}\nset_property used_in_implementation false [get_files {'+xdc.as_posix()+'}]\nsynth_design -top ai7030_edif_top')
t=t.replace((W/'synth.dcp').as_posix(),(W/'synth-r2.dcp').as_posix())
(E/'synthesis-r2.tcl').write_text(t)
