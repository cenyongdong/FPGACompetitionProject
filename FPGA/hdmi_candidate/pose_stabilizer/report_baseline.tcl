# Read-only reuse of the actual routed r45 checkpoint. No design mutation/implementation.
set_param general.maxThreads 2
open_checkpoint D:/FPGACompetitionProject/.local/hp2-deferred-consume-20261024-r45/pipeline-routed.dcp
set root U0_ps_ai_peripheral
foreach leaf {hp2_cycle_recorder hp2_protocol_recorder ai_read_path_monitor ai_path_monitor deferred_control hp2_protocol_observer startup_drain} {
 set cell [get_cells -hier -filter "NAME =~ */$leaf || NAME == $root/$leaf"]
 if {[llength $cell]!=1} {error "Expected one r45 baseline cell $leaf"}
 report_utilization -cells $cell -file $leaf.rpt
}
report_utilization -file r45-total.rpt
exit
