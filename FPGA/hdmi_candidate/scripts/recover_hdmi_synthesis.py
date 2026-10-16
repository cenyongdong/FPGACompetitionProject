"""Recover completed r2 child synthesis after outer session interruption; never reset it."""
from pathlib import Path
import json,hashlib,zipfile,shutil,sys
R=Path(__file__).resolve().parents[3];W=R/'.local/hdmi-integration-20261016-r1';E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1';F=W/'reference'
old=E/'system-synthesis-r2'
assert not (old/'execution.json').exists(),'Original stage has a result; review it instead'
log=(F/'fpai_demo_vivado.runs/synth_1/runme.log').read_text(encoding='utf-8',errors='replace')
assert 'synth_design completed successfully' in log and 'ERROR:' not in log
parent=(old/'stdout.txt').read_text(encoding='utf-8',errors='replace')
assert 'HDMI_TOP_SYNTHESIS_STATUS synth_design Complete!' in parent
src=F/'fpai_demo_vivado.runs/synth_1/ai7030_edif_top.dcp'
with zipfile.ZipFile(src) as z:assert z.testzip() is None
checks={}
def check(a,b):
 ha=hashlib.sha256(a.read_bytes()).hexdigest();hb=hashlib.sha256(b.read_bytes()).hexdigest();assert ha==hb,str(a)
 checks[str(a.relative_to(F))]=ha
for p in (E/'topology-revision-r2/r2-integrated-rtl').iterdir():check(F/'rtl/hdmi_candidate'/p.name,p)
check(F/'rtl/display/frame_to_ps_largebuf.v',E/'topology-revision-r2/frame_to_ps_largebuf-r2.v')
for name in ['ai7030_edif_top.v','ps_ai_peripheral.sv','display/uihdmitx.v','display/oserdese2_10to1.v']:
 check(F/'rtl'/name,E/'modified-reference-rtl'/name)
D=E/'r2-synthesis-recovery-inputs';D.mkdir(exist_ok=False)
shutil.copyfile(src,D/src.name)
for name in ['runme.log','ai7030_edif_top.vds','ai7030_edif_top.tcl']:
 p=src.parent/name
 if p.exists():shutil.copyfile(p,D/name)
result={'r2_child_synthesis_completed':True,'original_outer_exit_status':'not recorded; session interrupted during metadata/checkpoint collection',
 'original_execution_json_not_fabricated':True,'DCP_zip_crc_pass':True,'DCP_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
 'source_snapshot_checks':checks,'recovery_action':'open existing completed synth run and collect reports; do not reset or rerun synthesis'}
(D/'review.json').write_text(json.dumps(result,indent=2)+'\n')
sys.path.insert(0,str(W));import integration_support as s
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 set sr [get_runs synth_1]
 set f [open {@@OUT@@/run-state.txt} w]
 puts $f "STATUS|[get_property STATUS $sr]"
 puts $f "NEEDS_REFRESH|[get_property NEEDS_REFRESH $sr]"
 close $f
 if {![string match {*Complete*} [get_property STATUS $sr]]} {error "Recovered synthesis no longer Complete"}
 if {[get_property NEEDS_REFRESH $sr]} {error "Recovered synthesis needs refresh; do not silently reuse"}
 open_run synth_1
 report_utilization -file {@@OUT@@/utilization.rpt}
 report_clocks -file {@@OUT@@/clocks.rpt}
 set cells [get_cells -hier -filter {NAME =~ *hdmi_display*}]
 set f [open {@@OUT@@/HDMI-cells.txt} w]
 foreach c $cells {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 set f [open {@@OUT@@/HDMI-registers-and-clocks.txt} w]
 foreach c $cells {if {[string match FD* [get_property REF_NAME $c]]} {puts $f "$c|[get_property REF_NAME $c]|[get_clocks -quiet -of_objects [get_pins -quiet $c/C]]"}}
 close $f
 set f [open {@@OUT@@/global-MMCM.txt} w]
 foreach c [get_cells -hier -filter {REF_NAME == MMCME2_ADV}] {puts $f "$c|[get_property REF_NAME $c]"}
 close $f
 close_project
 puts "HDMI_R2_SYNTH_METADATA_RECOVERED_NO_RESYNTHESIS"
} result]} {puts "HDMI_RECOVERY_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('recover-synthesis-r2',tcl,ceiling=360,run_names=['synth_1'])
