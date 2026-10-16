"""Bind and inspect new CDC constraints against actual synthesized objects."""
from pathlib import Path
import sys,json,shutil,xml.etree.ElementTree as ET,hashlib
R=Path(__file__).resolve().parents[3];W=R/'.local/hdmi-integration-20261016-r1';E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1';F=W/'reference'
revision=sys.argv[1] if len(sys.argv)>1 else 'r1';assert revision in ('r1','r2','r3','r4','r5')
prerequisite=E/('system-synthesis' if revision=='r1' else 'system-synthesis-r2')/'execution.json'
if revision=='r5':
 prerequisite=E/'system-synthesis-r4/execution.json'
 assert json.loads((R/'tools/pose-v1/evidence/hdmi-candidate-sim-20261015-r8/result.json').read_text())['passed']
if revision in ('r2','r3','r4') and not prerequisite.exists():
 prerequisite=E/'recover-synthesis-r2/execution.json'
 assert json.loads((E/'r2-synthesis-recovery-inputs/review.json').read_text())['DCP_zip_crc_pass']
assert json.loads(prerequisite.read_text())['exit']==0
assert json.loads((E/'sim-phy-r2/result.json').read_text())['passed']
def params(p):
 out={}
 for n in ET.parse(p).getroot().iter():
  if n.tag.split('}')[-1]=='configurableElementValue':
   name=next((v for k,v in n.attrib.items() if k.split('}')[-1]=='referenceId'),None)
   if name and not name.startswith(('RUNTIME_PARAM.','PROJECT_PARAM.')):out[name]=n.text
 return out
source=R/'Docs/26嵌赛开发/fpai_demo_fpga';checked=[]
for p in source.rglob('*.xci'):
 rel=p.relative_to(source);assert params(p)==params(F/rel),str(rel);checked.append(rel.as_posix())
immutable=[]
for ext in ('*.prj','*.bd','*.edf','*.edif'):
 for p in source.rglob(ext):
  rel=p.relative_to(source);assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256((F/rel).read_bytes()).digest(),str(rel);immutable.append(rel.as_posix())
contract=E/('post-synthesis-IP-contract.json' if revision=='r1' else 'post-synthesis-IP-contract-'+revision+'.json')
assert not contract.exists(),'Preserve previous contract observation'
contract.write_text(json.dumps({'XCI_contracts':checked,'unchanged_DDR_BD_EDIF':immutable,'gate_pass':True,'synthesis_prerequisite':str(prerequisite)},indent=2)+'\n')
shutil.copyfile(R/'FPGA/hdmi_candidate/constraints/hdmi_cdc.xdc',F/'constrs_1/hdmi_cdc.xdc')
sys.path.insert(0,str(W));import integration_support as s
tcl=r'''
if {[catch {
 open_project {@@REF@@/fpai_demo_vivado.xpr}
 set_param general.maxThreads 2
 if {![llength [get_files -quiet {@@REF@@/constrs_1/hdmi_cdc.xdc}]]} {add_files -fileset constrs_1 -norecurse {@@REF@@/constrs_1/hdmi_cdc.xdc}}
 set xdc [get_files {@@REF@@/constrs_1/hdmi_cdc.xdc}]
 set_property USED_IN_SYNTHESIS false $xdc
 set_property PROCESSING_ORDER LATE $xdc
 open_run synth_1
 source {@@REF@@/constrs_1/hdmi_cdc.xdc}
 report_exceptions -coverage -file {@@OUT@@/exceptions-coverage.rpt}
 report_exceptions -ignored -file {@@OUT@@/exceptions-ignored.rpt}
 set command [hdmi_cdc_cells {scanout/core/core/mailbox/payload_hold_reg\[[0-9]+\]} 1]
 set response [hdmi_cdc_cells {scanout/core/core/mailbox/response_hold_reg\[[0-9]+\]} 1]
 set capture [hdmi_cdc_cells {scanout/core/core/mailbox/source_response_reg\[[0-9]+\]} 1]
 set mem_clock [get_clocks -of_objects [hdmi_cdc_pins [lindex $response 0] C]]
 set memory_regs [filter [all_registers -clock $mem_clock] {NAME =~ U0_ps_ai_peripheral/hdmi_display/*}]
 set f [open {@@OUT@@/mailbox-bound-check.txt} w]
 foreach item [list [list command $command $memory_regs 5.000] [list response $response $capture 10.000]] {
  lassign $item name src dst expected
  set paths [get_timing_paths -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20]
  if {![llength $paths]} {error "HDMI_MAILBOX_BOUND_IGNORED $name"}
  foreach p $paths {
   set req [get_property REQUIREMENT $p]
   if {abs($req-$expected)>0.001} {error "HDMI_MAILBOX_BOUND_WRONG $name $req"}
   puts $f "$name|requirement=$req|[get_property STARTPOINT_PIN $p]|[get_property ENDPOINT_PIN $p]"
  }
  report_timing -from [hdmi_cdc_pins $src C] -to [hdmi_cdc_pins $dst D] -max_paths 20 -file "@@OUT@@/mailbox-$name.rpt"
 }
 close $f
 if {[llength [info commands hdmi_cdc_cells]] && [string match *r5* {@@OUT@@}]} {
  set f [open {@@OUT@@/FIFO-local-reset-drivers.txt} w]
  set state [get_cells -hier -regexp {^U0_ps_ai_peripheral/hdmi_display/scanout/fifo/(wr_bin|wr_gray|rd_bin|rd_gray|wr_sync1|wr_sync2|rd_sync1|rd_sync2|lane)_reg\[[0-9]+\]$}]
  if {[llength $state]<40} {error "HDMI_FIFO_STATE_MISSING"}
  foreach c $state {
   set clear [hdmi_cdc_pins $c CLR]
   if {[llength $clear]!=1} {error "HDMI_FIFO_RESET_PIN_MISSING $c"}
   set drivers [all_fanin -flat -startpoints_only -only_cells -to $clear]
   if {[llength $drivers]!=1 || ![regexp {/fifo/(wr|rd)_release_reg\[2\]$} $drivers]} {error "HDMI_FIFO_RESET_NOT_LOCAL $c $drivers"}
   set src $drivers
   set src_clock [get_clocks -of_objects [hdmi_cdc_pins $src C]]
   set dst_clock [get_clocks -of_objects [hdmi_cdc_pins $c C]]
   if {$src_clock ne $dst_clock || [llength $src_clock]!=1} {error "HDMI_FIFO_RESET_DOMAIN_MISMATCH $c $drivers $src_clock $dst_clock"}
   puts $f "$c|$drivers|clock=$dst_clock"
  }
  close $f
  puts "HDMI_FIFO_STATE_RESET_LOCAL_CLOCK_PROOF [llength $state]"
 }
 report_cdc -details -file {@@OUT@@/CDC.rpt}
 report_drc -file {@@OUT@@/DRC.rpt}
 report_timing_summary -report_unconstrained -file {@@OUT@@/timing-summary.rpt}
 write_checkpoint -force {@@OUT@@/hdmi-constrained-synth.dcp}
 close_project
 puts "HDMI_CDC_CONSTRAINT_BINDING_COMPLETED_REPORTS_REQUIRE_REVIEW"
} result]} {puts "HDMI_CONSTRAINT_BIND_FAILED $result";puts $::errorInfo;exit 1}
exit
'''
s.stage('constraint-binding' if revision=='r1' else 'constraint-binding-'+revision,tcl,ceiling=540,run_names=['synth_1'])
