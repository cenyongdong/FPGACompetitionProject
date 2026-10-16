"""Continue the reviewed routed run through unchanged factory bit hooks."""
from pathlib import Path
import sys, json, hashlib

R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-integration-20261016-r1'
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
revision = sys.argv[1] if len(sys.argv)>1 else 'r5'
assert revision in ('r4','r5')
review = json.loads((E / ('system-route-' + revision) / 'review.json').read_text())
assert review['bit_generation_prerequisite_pass']
assert json.loads((E / ('system-route-' + revision) / 'execution.json').read_text())['exit'] == 0
if revision=='r5':
    assert json.loads((E / 'system-route-r5-reports/execution.json').read_text())['exit']==0
sources = json.loads((E / 'constraint-binding-r5/review.json').read_text())['bound_source_sha256']
for relative, expected in sources.items():
    assert hashlib.sha256((W / 'reference' / relative).read_bytes()).hexdigest() == expected, relative
assert hashlib.sha256((W / 'reference/constrs_1/hdmi_cdc.tcl').read_bytes()).hexdigest() == sources['constrs_1/hdmi_cdc.xdc']
sys.path.insert(0, str(W))
import integration_support as s
tcl = r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set nr [get_runs impl_hdmi_@@REV@@]
 if {![string match {*route_design Complete*} [get_property STATUS $nr]]} {error "Reviewed routed run missing"}
 if {[get_property NEEDS_REFRESH $nr]} {error "Routed run needs refresh"}
 if {[file exists {@@REF@@/fpai_demo_vivado.runs/impl_hdmi_@@REV@@/ai7030_edif_top.bit}]} {error "Preserve existing bit; do not overwrite"}
 current_run -implementation $nr
 launch_runs impl_hdmi_@@REV@@ -to_step write_bitstream -jobs 1
 wait_on_run impl_hdmi_@@REV@@
 set status [get_property STATUS $nr]
 puts "HDMI_WRITE_BITSTREAM_STATUS $status"
 if {![string match {*write_bitstream Complete*} $status]} {error "Bit generation not complete"}
 set f [open {@@OUT@@/actual-bit-products.txt} w]
 foreach p [glob -nocomplain {@@REF@@/fpai_demo_vivado.runs/impl_hdmi_@@REV@@/*.bit}] {puts $f "$p|[file size $p]"}
 close $f
 close_project
 puts "HDMI_RAW_BIT_COMPLETE_NOT_BOARD_ACCEPTANCE"
} result]} {puts "HDMI_WRITE_BITSTREAM_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('system-bit-'+revision, tcl.replace('@@REV@@',revision), ceiling=540, run_names=['impl_hdmi_'+revision])
