"""Reinstate only the existing four-rule factory session profile; report only."""
from pathlib import Path
import hashlib,json,re,types
R=Path(__file__).resolve().parents[3];S=Path(__file__).parent;START=Path(__file__).read_bytes()
E=R/'tools/pose-v1/evidence/hdmi-live-20261018-r9';W=R/'.local/hdmi-live-20261018-r9'
REF=W/'reference';AUX=REF/'fpai_demo_vivado.runs/report_drc_v3r9_r2'
STAGE='read-v3r9-factory-drc-r2';OUT=E/STAGE
RULES=['REQP-44','REQP-46','REQP-52','REQP-56']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):
 with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,indent=2)
def module(name,expected):
 p=S/name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected
 m=types.ModuleType('factory_drc_'+name.replace('.','_'));m.__file__=str(p)
 exec(compile(raw,str(p),'exec'),m.__dict__);return m

def main():
 reports=module('continue_hdmi_reader_boundary_reports.py','528fa208e01a3de18f3f312ce929458ea5c94dc59845dae2e4f036bf79f00967')
 proof,h,gate=reports.inputs()
 assert load(E/'formal-independent-route-r1/execution.json')['exit']==1
 assert 'factory DRC profile has errors' in (E/'formal-independent-route-r1/stderr.txt').read_text()
 assert load(reports.OUT/'phase-review.json')['passed']
 native=reports.NATIVE/'ai7030_edif_top_drc_routed.rpt'
 assert re.findall(r'^(\S+#\d+) Error$',native.read_text(),re.M)==['REQP-52#1','REQP-56#1']
 hooks={name:sha(REF/'ip_patch/process_control'/name) for name in ['implementation_opt_pre.tcl','write_bitstream_pre.tcl']}
 for name in hooks:
  text=(REF/'ip_patch/process_control'/name).read_text()
  for rule in RULES:assert re.search(r'set_property\s+IS_ENABLED\s+0\s+\[get_drc_checks\s+'+rule+r'\]',text)
 assert not OUT.exists() and not (W/STAGE).exists() and not AUX.exists()
 AUX.mkdir()
 base=reports.frozen('continue_ai_read_checkpoint.py')
 header,route,endpoints,body=base.pieces()
 endpoints=endpoints.replace('@@EVIDENCE@@',reports.E3.as_posix())
 base.E,base.W,base.REF,base.NATIVE=E,W,REF,AUX
 base.pieces=lambda:(header,route,endpoints,body)
 tcl=endpoints+'\n'+base.common_tcl(reports.ROUTED,audit=False)+r'''
set f [open {@@OUT@@/exact-existing-factory-profile.txt} {WRONLY CREAT EXCL}]
foreach rule {REQP-44 REQP-46 REQP-52 REQP-56} {
 set object [get_drc_checks $rule]
 puts $f "$rule|before|[get_property IS_ENABLED $object]"
 set_property IS_ENABLED 0 $object
 puts $f "$rule|after|[get_property IS_ENABLED $object]"
}
close $f
report_drc -file {@@OUT@@/factory-DRC.rpt}
check_managed_ps
close_design
puts "R9_EXISTING_FACTORY_DRC_PROFILE_REPORT_ONLY_COMPLETE"
'''
 tcl=base.substitutions(tcl)
 assert not re.search(r'^\s*(?:route_design|place_design|phys_opt_design|write_bitstream|opt_design|launch_runs|reset_run)\b',tcl,re.M)
 tcl='if {[catch {\n'+tcl+'\n} result]} {puts $result;puts $::errorInfo;exit 1}\nexit\n'
 owner=reports.frozen('eda_owned_stage.py');owner.E,owner.W=E,W
 try:owner.stage(STAGE,tcl,ceiling=360,run_names=[AUX.name])
 finally:
  if OUT.exists():
   (OUT/'actual-dispatcher.py').write_bytes(START);save(OUT/'input-proof.json',proof)
   save(OUT/'original-factory-hook-SHA256.json',hooks)
 assert reports.inputs()[0]==proof and Path(__file__).read_bytes()==START
 text=(OUT/'factory-DRC.rpt').read_text()
 assert not re.findall(r'^\S+#\d+ Error$',text,re.M)
 assert re.findall(r'^The following rules are disabled: ([^\r\n]+)',text,re.M)==[', '.join(RULES)]
 profile=(OUT/'exact-existing-factory-profile.txt').read_text().splitlines()
 assert profile==[item for rule in RULES for item in [rule+'|before|1',rule+'|after|0']]
 save(OUT/'phase-review.json',dict(passed=True,mode='existing_factory_DRC_report',
   source_routed_checkpoint=proof['routed_checkpoint'],factory_DRC_path=str(OUT/'factory-DRC.rpt'),
   factory_DRC_SHA256=sha(OUT/'factory-DRC.rpt'),factory_profile_errors=0,
   original_native_default_DRC_path=str(native),original_native_default_DRC_SHA256=sha(native),
   original_default_errors_retained=['REQP-52#1','REQP-56#1'],restored_existing_disabled_rules=RULES,
   original_factory_hook_SHA256=hooks,implementation_reexecuted=False,new_timing_or_DRC_waiver=False,
   actual_dispatcher_SHA256=hashlib.sha256(START).hexdigest(),board_executed=False))
 print('R9_EXISTING_FACTORY_PROFILE_DRC_PASS')

if __name__=='__main__':main()
