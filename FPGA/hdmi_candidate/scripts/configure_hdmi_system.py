"""Register new full-system RTL/clock constraints, check syntax and IP state."""
from pathlib import Path
import sys,json,shutil
R=Path(__file__).resolve().parents[3];W=R/'.local/hdmi-integration-20261016-r1';E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
assert json.loads((E/'integration-wiring.json').read_text())['all_other_RTL_unchanged']
F=W/'reference';xdc=F/'constrs_1/hdmi_input.xdc'
xdc.write_text('''# Independent Lite PL oscillator, schematic AC14 / BANK12 / 3.3V.
set_property PACKAGE_PIN AC14 [get_ports hdmi_ref_100m]
set_property IOSTANDARD LVCMOS33 [get_ports hdmi_ref_100m]
create_clock -name hdmi_ref_100m -period 10.000 [get_ports hdmi_ref_100m]
''',encoding='ascii');shutil.copyfile(xdc,E/xdc.name)
sys.path.insert(0,str(W));import integration_support as s
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 add_files -norecurse [glob {@@REF@@/rtl/hdmi_candidate/*}]
 add_files -fileset constrs_1 -norecurse {@@REF@@/constrs_1/hdmi_input.xdc}
 set_property TOP ai7030_edif_top [get_filesets sources_1]
 update_compile_order -fileset sources_1
 report_ip_status -file {@@OUT@@/IP-status.rpt}
 foreach ip [get_ips -all] {
  if {[get_property IS_LOCKED $ip]} {error "Locked IP encountered: $ip"}
 }
 set f [open {@@OUT@@/source-order.txt} w]
 foreach x [get_files -compile_order sources -used_in synthesis] {puts $f $x}
 close $f
 set f [open {@@OUT@@/runs.txt} w]
 foreach r [get_runs] {puts $f "$r|[get_property STATUS $r]|[get_property NEEDS_REFRESH $r]|[get_property DIRECTORY $r]"}
 close $f
 check_syntax -fileset sources_1
 close_project
 puts "HDMI_SYSTEM_SOURCE_SYNTAX_AND_IP_STATUS_COMPLETED"
} result]} {puts "HDMI_CONFIGURE_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('configure-and-syntax',tcl,ceiling=360)
