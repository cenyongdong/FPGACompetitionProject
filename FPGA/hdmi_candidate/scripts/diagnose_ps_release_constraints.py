"""Inspect only the missing recorder timing paths from the valid linked DCP."""
from prepare_ps_release_candidate import W,E,S,wrap
t='open_checkpoint {'+(W/'linked.dcp').as_posix()+'}\n'
t+='catch {source {'+(S/'pre-opt.tcl').as_posix()+'}} setup_error\nputs "SETUP_RESULT=$setup_error"\n'
t+=r'''
set f [open {@@E@@/missing-paths.tsv} w]
foreach pin $metaD {
 set p [get_timing_paths -to $pin -max_paths 1]
 puts $f "PIN\t$pin\tPATHS=[llength $p]"
 foreach start [all_fanin -flat -startpoints_only -to $pin] {
  puts $f "START\t$start\tCLOCK=[get_clocks -quiet -of_objects $start]"
 }
 if {[llength $p]} {puts $f "PATH\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"}
}
close $f
report_exceptions -ignored -file {@@E@@/ignored-exceptions.rpt}
write_checkpoint -force {@@W@@/preopt-diagnostic.dcp}
'''
t=t.replace('@@E@@',E.as_posix()).replace('@@W@@',W.as_posix())
(E/'diagnose-constraints.tcl').write_text(wrap(t))
