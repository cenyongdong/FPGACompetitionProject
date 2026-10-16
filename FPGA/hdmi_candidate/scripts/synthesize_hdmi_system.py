"""Synthesize changed top only, reusing qualified same-configuration IP runs."""
from pathlib import Path
import sys,json,shutil,hashlib
R=Path(__file__).resolve().parents[3];W=R/'.local/hdmi-integration-20261016-r1';E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
revision=sys.argv[1] if len(sys.argv)>1 else 'r1';assert revision in ('r1','r2','r4')
for path in ['sim-router-r2/result.json','sim-phy/result.json']:
 assert json.loads((E/path).read_text())['passed']
assert 'ERROR:' not in (E/'configure-and-syntax/stdout.txt').read_text(encoding='utf-8',errors='replace')
if revision=='r2':
 assert json.loads((E/'sim-phy-r3/result.json').read_text())['passed']
 assert (E/'topology-revision-r2/r1-synthesis-run-manifest.json').exists()
if revision=='r4':
 assert json.loads((R/'tools/pose-v1/evidence/hdmi-candidate-sim-20261015-r8/result.json').read_text())['passed']
 assert (E/'fifo-reset-revision-r4/before-run-manifest.json').exists()
# Recheck frozen original source and the nine candidate functional modules.
manifest=json.loads((R/'tools/pose-v1/evidence/hdmi-system-20261015-r1/original-manifest.json').read_text())
source=R/'Docs/26嵌赛开发/fpai_demo_fpga'
assert all(hashlib.sha256((source/n).read_bytes()).hexdigest()==h for n,h in manifest.items())
before=json.loads((E/'candidate-rtl-before.json').read_text())
for n,h in before.items():
 if revision=='r4' and n=='hdmi_stream_fifo.v':
  h=json.loads((E/'fifo-reset-revision-r4/decision.json').read_text())['new_fifo_sha256']
 assert hashlib.sha256((R/'FPGA/hdmi_candidate/rtl'/n).read_bytes()).hexdigest()==h,n
 copied=W/'reference/rtl/hdmi_candidate'/n
 if n in ('hdmi_clock_fmsh.v','hdmi_diff_output_fmsh.v','hdmi_diff_output_reference.v'):
  assert not copied.exists(),'Standalone physical primitive adapter is deliberately not used in factory full system'
 else:
  assert hashlib.sha256(copied.read_bytes()).hexdigest()==h,n
sys.path.insert(0,str(W));import integration_support as s
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set f [open {@@OUT@@/IP-prerequisites.txt} w]
 foreach r [get_runs *_synth_1] {puts $f "$r|[get_property STATUS $r]|[get_property NEEDS_REFRESH $r]"}
 close $f
 reset_run synth_1
 current_run -synthesis [get_runs synth_1]
 launch_runs synth_1 -jobs 1
 wait_on_run synth_1
 set status [get_property STATUS [get_runs synth_1]]
 puts "HDMI_TOP_SYNTHESIS_STATUS $status"
 if {![string match {*Complete*} $status]} {error "HDMI top synthesis did not complete"}
 open_run synth_1
 write_checkpoint -force {@@OUT@@/hdmi-system-synth.dcp}
 report_utilization -file {@@OUT@@/utilization.rpt}
 report_clocks -file {@@OUT@@/clocks.rpt}
 set cells [get_cells -hier -filter {NAME =~ *hdmi_display*}]
 if {[llength $cells]<100} {error "HDMI integrated cells missing"}
 set f [open {@@OUT@@/HDMI-cells.txt} w]
 foreach c $cells {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 set f [open {@@OUT@@/HDMI-registers-and-clocks.txt} w]
 foreach c $cells {
  set ref [get_property REF_NAME $c]
  if {[string match FD* $ref]} {
   puts $f "$c|$ref|[get_clocks -quiet -of_objects [get_pins -quiet $c/C]]"
  }
 }
 close $f
 close_project
 puts "HDMI_SYSTEM_SYNTHESIS_COMPLETED_NOT_BOARD_ACCEPTANCE"
} result]} {puts "HDMI_SYNTHESIS_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('system-synthesis' if revision=='r1' else 'system-synthesis-'+revision,tcl,run_names=['synth_1'])
