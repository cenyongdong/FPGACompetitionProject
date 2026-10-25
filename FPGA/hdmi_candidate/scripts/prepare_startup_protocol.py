from pathlib import Path
import re,json,shutil,sys
import argparse
parser=argparse.ArgumentParser(description='Prepare the connected observational startup diagnostic; no board operations')
parser.add_argument('--asset-root',type=Path,required=True);a=parser.parse_args()
O=a.asset_root.resolve();C=Path(__file__).resolve().parents[3]
W=O/'.local/hp2-startup-protocol-20261023-r37';E=O/'tools/pose-v1/evidence/hp2-startup-protocol-20261023-r37'
W.mkdir(parents=True,exist_ok=False);E.mkdir(parents=True,exist_ok=False)
W31=O/'.local/hdmi-protocol-checker-20261023-r31';E31=O/'tools/pose-v1/evidence/hdmi-protocol-checker-20261023-r31'
B=C/'FPGA/hdmi_candidate/baselines/ps_release_r26/sources';S=W/'sources';S.mkdir()
for p in (W31/'sources').glob('*'):
 if p.is_file():shutil.copyfile(p,S/p.name)
shutil.copyfile(W31/'registered-observer.sv',W/'registered-observer.sv')
p=S/'ps_ai_peripheral.sv';s=p.read_text();baseline=(B/'ps_ai_peripheral.sv').read_text()
def instance(text,begin):
 a=text.index(begin);end=re.search(r'(?m)^\s*\);',text[a:]);assert end,begin
 return a,a+end.end(),text[a:a+end.end()]
for name in ('frame_to_ps_largebuf #','hdmi_board hdmi_display('):
 a,b,_=instance(s,name);original=instance(baseline,name)[2];s=s[:a]+original+s[b:]
inputs=re.findall(r"(?m)^assign S_AXI_HP2_(\w+) = '0;\n",s);assert len(inputs)==27,inputs
s=re.sub(r"(?m)^assign S_AXI_HP2_\w+ = '0;\n",'',s)
s=s.replace('// r28 source isolation: retain both xbar slots and observe actual S01 outputs.\n// No request and no forced consumption of unknown R/B responses.','// r37: S01 HDMI and legacy video sources restored exactly to connected r26.')
assigns=re.findall(r'(?m)^\s*assign S_AXI_HP2_(\w+)\s*=([^;]+);',baseline)
for suffix,value in assigns:
 if suffix in inputs:
  existing=re.search(r'assign S_AXI_HP2_'+suffix+r'\s*=([^;]+);',s)
  if existing:
   assert existing.group(1).strip()==value.strip(),suffix
   continue
  s=s.replace('hdmi_board hdmi_display(',f'assign S_AXI_HP2_{suffix}={value};\nhdmi_board hdmi_display(',1)
def block(text,begin,end):return text[text.index(begin):text.index(end,text.index(begin))]
assert block(s,'AI_Mate ZGolo(','\nendmodule')==block(baseline,'AI_Mate ZGolo(','\nendmodule')
assert block(s,'frame_trans frame_trans_inst0(','ps_ai_wrapper ps_ai_wrapper_u0 (')==block(baseline,'frame_trans frame_trans_inst0(','ps_ai_wrapper ps_ai_wrapper_u0 (')
p.write_text(s,encoding='utf-8',newline='\n')
# Restore actual connected HDMI Gray/reset bounds; do not retain isolation-only folds.
shutil.copyfile(O/'.local/hdmi-boot-witness-20261019-r23/reference/constrs_1/hdmi_cdc.tcl',S/'hdmi_cdc.tcl')
shutil.copyfile(O/'.local/hdmi-boot-witness-20261019-r23/reference/constrs_1/ai_read_monitor_cdc.tcl',S/'ai_read_monitor_cdc.tcl')
def remap(t):return t.replace(W31.as_posix(),W.as_posix()).replace(E31.as_posix(),E.as_posix())
for p in S.glob('*.tcl'):p.write_text(remap(p.read_text()),encoding='utf-8',newline='\n')
for n in ('ps_release_cdc.tcl','ps_release_raw_flags_cdc.tcl'):
 p=S/n;p.write_text(p.read_text().replace('(7|10|12|13)','7'))
connected_flags=C/'FPGA/hdmi_candidate/constraints/connected_release_flags.tcl'
cut_scope=C/'FPGA/hdmi_candidate/constraints/hp2_existing_cut_scope.tcl'
p=S/'pre-opt.tcl';p.write_text(p.read_text()+'\nsource {'+cut_scope.as_posix()+'}\nsource {'+connected_flags.as_posix()+'}\n')

syn=remap((E31/'synthesis-registered-capacity8.tcl').read_text())
# Reuse the same generated native IP, no migration or regeneration.
syn=syn.replace((W/'ip-capacity8').as_posix(),(W31/'ip-capacity8').as_posix())
syn=syn.replace('synth-registered-capacity8.dcp','synth.dcp')
(E/'synthesis.tcl').write_text(syn,encoding='utf-8',newline='\n')
opt=remap((E31/'opt-registered-capacity8.tcl').read_text()).replace('synth-registered-capacity8.dcp','synth.dcp').replace('linked-unclocked-registered-capacity8.dcp','linked-unclocked.dcp').replace('linked-registered-capacity8.dcp','linked.dcp').replace('opt-registered-capacity8.dcp','opt.dcp')
start=opt.index('set x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4');end=opt.index('source {',start)
opt=opt[:start]+'''# Verify the formerly isolated master is connected in this actual linked netlist.
set x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4
foreach field {ARVALID ARADDR RREADY} {
 set p [get_pins -quiet $x/S01_AXI_[string tolower $field]*]
 if {![llength $p]} {error "Connected S01 input missing: $field"}
 set src [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $p] -filter {DIRECTION == OUT}]]
 set refs [lsort -unique [get_property REF_NAME $src]]
 puts "S01_CONNECTED $field $refs"
 if {$refs eq "GND" || ![llength $refs]} {error "S01 unexpectedly isolated: $field"}
}
'''+opt[end:]
(E/'opt.tcl').write_text(opt,encoding='utf-8',newline='\n')
place=remap((E31/'place-registered-capacity8-r2.tcl').read_text()).replace('opt-registered-capacity8.dcp','opt.dcp').replace('placed-registered-capacity8.dcp','placed.dcp').replace('physopt-registered-capacity8.dcp','physopt.dcp')
# Reuse the qualified connected design for incremental placement; same target/clocks.
place=place.replace('place_design -directive Explore','read_checkpoint -incremental {'+(O/'.local/hdmi-ps-release-20261020-r26/qualified-routed.dcp').as_posix()+'}\nplace_design -directive Explore')
(E/'place.tcl').write_text(place,encoding='utf-8',newline='\n')
route=remap((E31/'route-registered-capacity8.tcl').read_text()).replace('physopt-registered-capacity8.dcp','physopt.dcp').replace('routed-registered-capacity8.dcp','routed.dcp').replace('route-failed-registered-capacity8.dcp','route-failed.dcp')
(E/'route.tcl').write_text(route,encoding='utf-8',newline='\n')
final=remap((E31/'final-registered-capacity8.tcl').read_text()).replace('routed-registered-capacity8.dcp','routed.dcp').replace('qualified-registered-capacity8.dcp','qualified-routed.dcp')
connection_check='set connection_file [open {CONNECTION_FILE} w]\nset x U0_ps_ai_peripheral/ps_ai_wrapper_u0/ps_ai_i/axi_interconnect_4\nforeach field {ARVALID ARADDR RREADY} {\n set input [get_pins -quiet $x/S01_AXI_[string tolower $field]*]\n if {![llength $input]} {error "Connected actual S01 pin absent: $field"}\n set drivers [get_cells -of_objects [get_pins -leaf -of_objects [get_nets -segments -of_objects $input] -filter {DIRECTION == OUT}]]\n set refs [lsort -unique [get_property REF_NAME $drivers]]\n puts $connection_file "S01_CONNECTED\\t$field\\t$refs"\n if {![llength $refs] || $refs eq "GND"} {error "Actual connected S01 pin folded to zero: $field"}\n}\nset ps [get_cells -hier -filter {REF_NAME == PS7}]\nforeach field {SAXIHP2ARESETN SAXIHP2ARVALID SAXIHP2ARREADY SAXIHP2RVALID SAXIHP2RREADY} {\n set pin [get_pins -of_objects $ps -filter [format {REF_PIN_NAME == %s} $field]]\n if {[llength $pin]!=1} {error "Actual PS HP2 boundary missing: $field"}\n puts $connection_file "PS_BOUNDARY\\t$field\\t[get_property DIRECTION $pin]\\t[get_nets -of_objects $pin]"\n}\nclose $connection_file\n\n'
connection_check=connection_check.replace('CONNECTION_FILE',(E/'registered-capacity8-physical/source-connected-native.tsv').as_posix())
final=final.replace('write_checkpoint -force {',connection_check+'write_checkpoint -force {',1)
final=final.replace('report_timing_summary -file','source {'+cut_scope.as_posix()+'}\nsource {'+connected_flags.as_posix()+'}\nreport_timing_summary -file',1).replace('(7|10|12|13)','7')
(E/'final.tcl').write_text(final,encoding='utf-8',newline='\n')
(E/'registered-capacity8-physical/qualified-r8').mkdir(parents=True)
overlay=json.loads((E31/'source-overlay-registered-capacity8.json').read_text())
overlay['replacements']={k:remap(v.replace('\\','/')) for k,v in overlay['replacements'].items()}
overlay['additional_sources']=[str(W/'registered-observer.sv') if 'registered-observer.sv' in n else n for n in overlay['additional_sources']]
overlay.pop('S01_inputs_held_zero',None);overlay['S01_source_connected']=True
overlay['additional_constraint_sources']=[remap(n.replace('\\','/')) for n in overlay['additional_constraint_sources']]
overlay['additional_constraint_sources'] += [str(connected_flags), str(cut_scope)]
overlay.pop('source_isolation_not_xbar_removal',None)
overlay['scope']='Connected r26 functional S01, unchanged four AI HC and functional resets; passive first-indication witness plus non-recommendation-triggered full native checker window'
(E/'source-overlay.json').write_text(json.dumps(overlay,indent=2)+'\n')
state=dict(status='offline_startup_protocol_prepared',authorization='2026-10-23 user selected startup reset/protocol diagnosis; prior explicit PS diagnosis BOOT/reboot permission remains; old sessions closed',AI_four_HC_unchanged=True,S01_connected=True,functional_reset_changed=False,native_IP_reused=str(W31/'ip-capacity8/hp2_native_protocol_checker'),trigger_recommendations_preserved=True,SDK_Open=0,inference=0,HDMI_START=False,board_starts=0,next='Directed native IP and trigger tests, then actual physical qualification before any new board session.')
(E/'state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
print('Prepared connected diagnostic RTL and reused native IP/PS export; four AI and functional resets preserved.')
