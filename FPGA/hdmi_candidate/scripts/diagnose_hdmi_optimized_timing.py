"""Inspect a completed optimized DCP after bounded place optimization stop."""
from pathlib import Path
import sys, json, hashlib, shutil, zipfile

R = Path(__file__).resolve().parents[3]
W = R / '.local/hdmi-integration-20261016-r1'
E = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
assert (E / 'system-route-r3/stop-for-timing-diagnosis.json').exists()
assert json.loads((E / 'system-route-r3/execution.json').read_text())['exit'] != 0
O = E / 'optimized-timing-input-r3'
O.mkdir(exist_ok=False)
source = W / 'reference/fpai_demo_vivado.runs/impl_hdmi_r3/ai7030_edif_top_opt.dcp'
target = O / source.name
shutil.copyfile(source, target)
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
sha = hashlib.sha256(target.read_bytes()).hexdigest()
assert sha == hashlib.sha256(source.read_bytes()).hexdigest()
(O / 'identity.json').write_text(json.dumps({'source':str(source),'sha256':sha,
    'bytes':target.stat().st_size,'zip_crc_pass':True,'stage':'Optimized, NOT placed/routed'},indent=2)+'\n')
sys.path.insert(0, str(W))
import integration_support as s
tcl = r'''
if {[catch {
 set_param general.maxThreads 2
 open_checkpoint {@@INPUT@@}
 report_timing_summary -report_unconstrained -file {@@OUT@@/timing-summary.rpt}
 report_timing -max_paths 30 -file {@@OUT@@/global-setup.rpt}
 report_timing -delay_type min -max_paths 20 -file {@@OUT@@/global-hold.rpt}
 set hdmi [get_cells -hier -filter {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 report_timing -to $hdmi -max_paths 30 -file {@@OUT@@/HDMI-setup.rpt}
 report_timing -to $hdmi -delay_type min -max_paths 20 -file {@@OUT@@/HDMI-hold.rpt}
 report_exceptions -ignored -file {@@OUT@@/exceptions-ignored.rpt}
 report_clocks -file {@@OUT@@/clocks.rpt}
 close_design
 puts "HDMI_OPTIMIZED_TIMING_DIAGNOSIS_COMPLETE_NOT_ROUTED_ACCEPTANCE"
} result]} {puts "HDMI_TIMING_DIAGNOSIS_FAILED $result";puts $::errorInfo;exit 1}
exit
'''.replace('@@INPUT@@', target.as_posix())
s.stage('optimized-timing-diagnosis-r3', tcl, ceiling=360, run_names=['impl_hdmi_r3'])
