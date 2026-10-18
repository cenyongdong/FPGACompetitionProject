"""Configure/synthesize the isolated observer candidate; never changes board state."""
from pathlib import Path
import importlib.util,json,shutil,sys
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-live-20261017-r1';W=R/'.local/hdmi-live-20261017-r1'
assert json.loads((E/'monitor-candidate-preparation.json').read_text())['AI_DDR_logic_unchanged']
spec=importlib.util.spec_from_file_location('eda_support',W/'eda_support.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
mode=sys.argv[1];assert mode in ['configure','synthesis','constraints']
if mode=='configure':
    shutil.copyfile(R/'FPGA/hdmi_candidate/diagnostics/ai_monitor_cdc.tcl',W/'reference/constrs_1/ai_monitor_cdc.tcl')
    hook=W/'reference/ip_patch/process_control/implementation_opt_pre_hdmi.tcl'
    s=hook.read_text(encoding='utf-8');assert 'ai_monitor_cdc' not in s
    s+='\nsource [file normalize [file join [file dirname [info script]] ../../constrs_1/ai_monitor_cdc.tcl]]\n'
    hook.write_text(s,encoding='utf-8')
    tcl=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
add_files -norecurse {@@REF@@/rtl/hdmi_candidate/ai_event_monitor.sv}
set_property FILE_TYPE SystemVerilog [get_files *ai_event_monitor.sv]
update_compile_order -fileset sources_1
check_syntax -fileset sources_1
set f [open {@@OUT@@/IP-prerequisites.txt} w]
foreach r [get_runs *_synth_1] {puts $f "$r|[get_property STATUS $r]|[get_property NEEDS_REFRESH $r]"}
close $f
set f [open {@@OUT@@/compile-order.txt} w]
foreach p [get_files -compile_order sources -used_in synthesis] {puts $f $p}
close $f
close_project
puts "AI_MONITOR_ISOLATED_SYNTAX_COMPLETE_NO_BOARD_OPERATION"
'''
elif mode=='synthesis':
    assert json.loads((E/'monitor-configure/execution.json').read_text())['exit']==0
    prerequisites=(E/'monitor-configure/IP-prerequisites.txt').read_text().splitlines()
    assert len(prerequisites)>=20 and all('Complete' in row and row.endswith('|0') for row in prerequisites),prerequisites
    tcl=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
reset_run synth_1
current_run -synthesis [get_runs synth_1]
launch_runs synth_1 -jobs 1
wait_on_run synth_1
set status [get_property STATUS [get_runs synth_1]]
puts "AI_MONITOR_SYNTHESIS_STATUS $status"
if {![string match {*Complete*} $status]} {error "AI monitor top synthesis failed"}
open_run synth_1
write_checkpoint {@@OUT@@/ai-monitor-synth.dcp}
report_utilization -file {@@OUT@@/utilization.rpt}
report_clocks -file {@@OUT@@/clocks.rpt}
set c [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/ai_path_monitor/*}]
if {[llength $c]<500} {error "Observer cells absent"}
set f [open {@@OUT@@/observer-count.txt} w];puts $f [llength $c];close $f
close_project
puts "AI_MONITOR_SYNTHESIS_COMPLETE_NOT_TIMING_OR_BOARD_ACCEPTANCE"
'''
else:
    assert json.loads((E/'monitor-synthesis/execution.json').read_text())['exit']==0
    tcl=r'''
open_project {@@REF@@/fpai_demo_vivado.xpr}
set_param general.maxThreads 2
open_run synth_1
source {@@REF@@/constrs_1/hdmi_cdc.tcl}
source {@@REF@@/constrs_1/ai_monitor_cdc.tcl}
report_timing -from [hdmi_cdc_pins $ai_source C] -to [hdmi_cdc_pins $ai_capture D] -max_paths 2 -file {@@OUT@@/observer-snapshot-path.rpt}
report_utilization -file {@@OUT@@/utilization.rpt}
close_project
puts "AI_MONITOR_CONSTRAINT_BINDING_COMPLETE_NOT_ROUTED_ACCEPTANCE"
'''
tcl='if {[catch {\n'+tcl+'\n} result]} {puts "AI_MONITOR_BUILD_FAILED $result";puts $::errorInfo;exit 1}\nexit\n'
m.stage('monitor-'+mode,tcl,ceiling=1800 if mode=='synthesis' else 540,run_names=['synth_1'] if mode=='synthesis' else [])
