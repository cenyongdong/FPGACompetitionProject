"""Continue the reviewed routed run through unchanged factory bit hooks."""
from pathlib import Path
import sys, json, hashlib

R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-integration-20261016-r1'
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
review = json.loads((E / 'system-route-r4/review.json').read_text())
assert review['bit_generation_prerequisite_pass']
assert json.loads((E / 'system-route-r4/execution.json').read_text())['exit'] == 0
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
 set nr [get_runs impl_hdmi_r4]
 if {![string match {*route_design Complete*} [get_property STATUS $nr]]} {error "Reviewed routed run missing"}
 if {[get_property NEEDS_REFRESH $nr]} {error "Routed run needs refresh"}
 if {[file exists {@@REF@@/fpai_demo_vivado.runs/impl_hdmi_r4/ai7030_edif_top.bit}]} {error "Preserve existing bit; do not overwrite"}
 current_run -implementation $nr
 launch_runs impl_hdmi_r4 -to_step write_bitstream -jobs 1
 wait_on_run impl_hdmi_r4
 set status [get_property STATUS $nr]
 puts "HDMI_WRITE_BITSTREAM_STATUS $status"
 if {![string match {*write_bitstream Complete*} $status]} {error "Bit generation not complete"}
 set f [open {@@OUT@@/actual-bit-products.txt} w]
 foreach p [glob -nocomplain {@@REF@@/fpai_demo_vivado.runs/impl_hdmi_r4/*.bit}] {puts $f "$p|[file size $p]"}
 close $f
 close_project
 puts "HDMI_RAW_BIT_COMPLETE_NOT_BOARD_ACCEPTANCE"
} result]} {puts "HDMI_WRITE_BITSTREAM_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('system-bit-r4', tcl, ceiling=540, run_names=['impl_hdmi_r4'])
