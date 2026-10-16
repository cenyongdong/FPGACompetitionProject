"""Bounded post-elaboration import of the actual vendor-translated PS netlist.
No place/route, bitstream, download, or assertion of physical AI binding.
"""
from pathlib import Path
import json,os,shutil,subprocess,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/procise-ps-import';W=R/'.local/hdmi-vivado2018-20261016-r2/procise-ps-import'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
prior=E.parent/'translate-ps'
assert json.loads((prior/'conversion-contract-review.json').read_text(encoding='utf-8'))['AI_port_names_connections_and_values_preserved']
shutil.copyfile(prior/'converted/actual_ps.edf',W/'actual_ps.edf')
tcl='''
if {[catch {
 create_project -name imported_ps -device JFMQL30TAI676H
 add_design_file -file actual_ps.edf
 set_top -top ps_ai_processing_system7_0_0
 save_project
 load_design -stage_post_elaborate -no_hier
 puts "NATIVE_REAL_PS_EDIF_POST_ELABORATE_COMPLETE"
} result]} {puts "NATIVE_REAL_PS_EDIF_IMPORT_FAILED $result";exit 1}
exit
'''
(W/'import.tcl').write_text(tcl,encoding='ascii');shutil.copyfile(W/'import.tcl',E/'import.tcl')
root=Path('C:/FudanMicro/Procise');env=os.environ.copy()
env.update(APP_DIR=str(root),ICTIME_HOME=str(root),FMSH_DB=str(root/'db'),TCL_LIBRARY=str(root/'tcl8.4'))
env['PATH']=str(root/'dll')+';'+str(root/'bin')+';'+env['PATH']
start=time.monotonic();code=None;timeout=False
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen([str(root/'bin/procise.exe'),'import.tcl'],cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr)
  try:code=p.wait(timeout=15)
  except subprocess.TimeoutExpired:pass
result={'exit':code,'seconds':time.monotonic()-start,'timeout':timeout,'budget_seconds':180,
 'target':'JFMQL30TAI676H','mode':'real_translated_EDIF_post_elaborate_only',
 'physical_PCPU7_AI_binding_verified':False,'full_system_or_hardware_acceptance':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
shutil.copytree(W,E/'returned-project')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-4500:],flush=True)
if code or timeout:raise SystemExit('Native translated PS netlist import failed; preserve and stop')
