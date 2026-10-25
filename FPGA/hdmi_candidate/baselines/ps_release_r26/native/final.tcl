if {[catch {
set_param general.maxThreads 2
open_checkpoint {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/routed-r8.dcp}
# The implementation installed the factory clock bindings and all CDC bounds; validate without reapplying. Do not reapply.
# The completed native route has positive setup/hold; validate that checkpoint directly.
set f [open {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/final-native-facts.tsv} w]
puts $f "PART	[get_property PART [current_project]]"
set pass 1
foreach mode {max min} {
 set p [get_timing_paths -delay_type $mode -max_paths 1]
 set slack [get_property SLACK $p]
 puts $f "$mode	$slack	[get_property STARTPOINT_PIN $p]	[get_property ENDPOINT_PIN $p]"
 if {$slack<0} {set pass 0}
}
set root {^U0_ps_ai_peripheral/ai_read_path_monitor/boot_history[./]witness/}
set src [get_cells -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $root]]
set dst_all [get_cells -hier -regexp [format {%scsr_snapshot_reg\[[0-9]+\]$} $root]]
set dst {}
foreach c $dst_all {regexp {\[([0-9]+)\]$} [get_property NAME $c] unused index;if {$index<384} {lappend dst $c}}
set srcC [get_pins -of_objects $src -filter {REF_PIN_NAME == C}]
set dstD [get_pins -of_objects $dst -filter {REF_PIN_NAME == D}]
set p [get_timing_paths -from $srcC -to $dstD -max_paths 1]
puts $f "OLD_BUS	[llength $src]	[llength $dst]	[get_property REQUIREMENT $p]	[get_property SLACK $p]"
if {[llength $src]!=374 || [llength $dst]!=374 || [get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-10)>0.001 || [get_property SLACK $p]<0} {set pass 0}
set metaD [get_pins -of_objects [get_cells -hier -regexp [format {%sflags_meta_reg\[[0-9]+\]$} $root]] -filter {REF_PIN_NAME == D}]
set paths [get_timing_paths -to $metaD -max_paths 5 -nworst 1]
if {[llength $metaD]!=5 || [llength $paths]!=5} {set pass 0}
foreach p $paths {
 puts $f "OLD_META	[get_property ENDPOINT_PIN $p]	[get_property REQUIREMENT $p]	[get_property SLACK $p]"
 if {[get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {set pass 0}
}
set ready [get_pins -hier -quiet -filter {NAME =~ */proc_sys_reset_1/dcm_locked}]
if {[llength $ready]!=1} {error "Routed HP2 readiness pin missing"}
set paths [get_timing_paths -through $ready -max_paths 4]
if {![llength $paths]} {error "New HP2 readiness paths absent or cut"}
foreach p $paths {
 puts $f "READY	[get_property STARTPOINT_PIN $p]	[get_property ENDPOINT_PIN $p]	[get_property REQUIREMENT $p]	[get_property SLACK $p]"
 if {[get_property SLACK $p]<0} {set pass 0}
}

set r {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/}
set s [get_cells -hier -regexp [format {%ssource_snapshot_reg\[[0-9]+\]$} $r]]
set d [get_cells -hier -regexp [format {%scsr_source_snapshot_reg\[[0-9]+\]$} $r]]
if {![llength $s] || [llength $s]!=[llength $d]} {error "New source/capture bus missing"}
set p [get_timing_paths -from [get_pins -of_objects $s -filter {REF_PIN_NAME == C}] -to [get_pins -of_objects $d -filter {REF_PIN_NAME == D}] -max_paths 1]
puts $f "NEW_BUS\t[llength $s]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
if {![llength $p] || abs([get_property REQUIREMENT $p]-10)>0.001 || [get_property SLACK $p]<0} {set pass 0}
set m {}
foreach c [get_cells -hier -regexp [format {%s(levels_meta_reg\[[0-9]+\]|beat_meta_reg)$} $r]] {
 if {![regexp {levels_meta_reg\[7\]$} [get_property NAME $c]]} {lappend m [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
}
if {[llength $m]<16} {set pass 0}
foreach pin $m {
 set p [get_timing_paths -to $pin -max_paths 1]
 if {![llength $p]} {error "Missing final first-stage path: $pin"}
 puts $f "NEW_META\t[get_property ENDPOINT_PIN $p]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {set pass 0}
}
set ps [get_cells -hier -filter {REF_NAME == PS7}]
set pin [get_pins -of_objects $ps -filter {REF_PIN_NAME == SAXIHP2ARESETN}]
set fanout [filter [all_fanout -flat -endpoints_only -from $pin] {NAME =~ *ai_read_path_monitor/release_history/*}]
puts $f "PSRESET\t$pin\t[llength $fanout]"
if {[llength $pin]!=1 || ![llength $fanout]} {set pass 0}
foreach clock {clk_fpga_0 clk_out1_clk_wiz_0 clk_pll_i} period {20 10 5} {
 set c [get_clocks $clock]
 puts $f "CLOCK\t$clock\t[get_property PERIOD $c]"
 if {[llength $c]!=1 || abs([get_property PERIOD $c]-$period)>0.001} {set pass 0}
}
set raw_D {}
foreach c [get_cells -hier -regexp {^U0_ps_ai_peripheral/ai_read_path_monitor/release_history/first_r_levels_reg\[[0-9]+\]$}] {
 if {![regexp {first_r_levels_reg\[7\]$} [get_property NAME $c]]} {lappend raw_D [get_pins -of_objects $c -filter {REF_PIN_NAME == D}]}
}
if {[llength $raw_D]<16} {error "Raw first-event capture missing"}
foreach pin $raw_D {
 set p [get_timing_paths -to $pin -max_paths 1]
 puts $f "NEW_RAW\t$pin\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"
 if {[get_property REQUIREMENT $p] eq "" || abs([get_property REQUIREMENT $p]-5)>0.001 || [get_property SLACK $p]<0} {set pass 0}
}

close $f
report_timing -through $ready -max_paths 4 -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/ready-timing.rpt}
report_timing_summary -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/timing-final.rpt} -max_paths 10 -report_unconstrained
report_pulse_width -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/pulse-width.rpt}
report_bus_skew -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/bus-skew-final.rpt}
report_route_status -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/route-status-final.rpt}
report_drc -file {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-ps-release-20261020-r26/qualified-r8/drc-final.rpt}
write_checkpoint -force {D:/FPGACompetitionProject/.local/hdmi-ps-release-20261020-r26/qualified-routed.dcp}
if {!$pass} {error "Physical timing/CDC prerequisites failed; preserve reports and DCP"}
puts "HP2_READY_FINAL_PHYSICAL_COMPLETE"
} result]} {puts "HP2_READY_FINAL_FAILED $result";puts $::errorInfo;exit 1}
exit
