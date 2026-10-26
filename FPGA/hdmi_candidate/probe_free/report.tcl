# Read-only physical qualification of the new uninstrumented design.
if {[catch {
set_param general.maxThreads 2
set work {D:/FPGACompetitionProject/.local/hdmi-probe-free-20261025-r1}
set out {D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-probe-free-20261025-r1/physical}
open_checkpoint $work/pipeline-routed.dcp
report_timing_summary -file $out/timing-final.rpt -max_paths 10 -report_unconstrained
report_pulse_width -file $out/pulse-width.rpt
report_bus_skew -file $out/bus-skew-final.rpt
report_route_status -file $out/route-status-final.rpt
report_drc -file $out/drc-final.rpt
report_utilization -hierarchical -file $out/utilization.rpt
report_cdc -details -cells [get_cells U0_ps_ai_peripheral/hdmi_display] -file $out/hdmi-cdc.rpt
report_clocks -file $out/clocks.rpt
set f [open $out/final-native-facts.tsv w]
puts $f "PART\t[get_property PART [current_project]]"
foreach mode {max min} {
 set p [get_timing_paths -delay_type $mode -max_paths 1]
 if {![llength $p]} {error "No $mode timing path"}
 puts $f "$mode\t[get_property SLACK $p]\t[get_property STARTPOINT_PIN $p]\t[get_property ENDPOINT_PIN $p]"
}
foreach instance {ai_path_monitor ai_read_path_monitor hp2_cycle_recorder hp2_protocol_recorder hp2_protocol_observer deferred_control startup_drain} {
 set cells [get_cells -quiet -hier -filter "NAME =~ U0_ps_ai_peripheral/$instance || NAME =~ U0_ps_ai_peripheral/$instance/*"]
 puts $f "REMOVED\t$instance\t[llength $cells]"
 if {[llength $cells]} {error "Diagnostic hierarchy remains: $instance"}
}
set cores [get_debug_cores -quiet]
puts $f "DEBUG_CORES\t[llength $cores]"
if {[llength $cores]} {error "Debug core remains"}
set marked [get_nets -quiet -hier -filter {MARK_DEBUG == 1}]
puts $f "MARK_DEBUG\t[llength $marked]"
foreach net $marked {puts $f "DEBUG_NET\t$net"}
if {[llength $marked]} {error "Marked probe nets remain"}
foreach clock {clk_fpga_0 clk_out1_clk_wiz_0 clk_pll_i} period {20 10 5} {
 set c [get_clocks -quiet $clock]
 if {[llength $c]!=1 || abs([get_property PERIOD $c]-$period)>0.001} {error "Functional clock changed: $clock"}
 puts $f "CLOCK\t$clock\t[get_property PERIOD $c]"
}
set ready [get_pins -hier -quiet -filter {NAME =~ */proc_sys_reset_1/dcm_locked}]
set paths [get_timing_paths -through $ready -max_paths 4]
if {[llength $ready]!=1 || ![llength $paths]} {error "Functional HP2 readiness path absent/cut"}
foreach p $paths {puts $f "READY\t[get_property STARTPOINT_PIN $p]\t[get_property ENDPOINT_PIN $p]\t[get_property REQUIREMENT $p]\t[get_property SLACK $p]"}
set x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4
foreach field {ARVALID ARADDR RREADY} {
 set pins [get_pins -quiet $x/S01_AXI_[string tolower $field]*]
 set src [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $pins] -filter {DIRECTION == OUT}]]
 set refs [lsort -unique [get_property REF_NAME $src]]
 puts $f "S01_CONNECTED\t$field\t$refs"
 if {![llength $pins] || ![llength $refs] || $refs eq "GND"} {error "Functional S01 disconnected: $field"}
}
close $f
} result]} {puts $result; puts $::errorInfo; exit 1}
exit
