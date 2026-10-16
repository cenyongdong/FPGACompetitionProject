"""Read the installed vendor netlist converter's help; no conversion/implementation."""
from pathlib import Path
import json,os,subprocess,time
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/translate-help';W=R/'.local/hdmi-vivado2018-20261016-r2/translate-help'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
root=Path('C:/FudanMicro/Procise');env=os.environ.copy()
env.update(APP_DIR=str(root),ICTIME_HOME=str(root),FMSH_DB=str(root/'db'),TCL_LIBRARY=str(root/'tcl8.4'))
env['PATH']=str(root/'dll')+';'+str(root/'bin')+';'+env['PATH']
start=time.monotonic();code=None;timeout=False;cleanup=None
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen([str(root/'bin/translate_file.exe'),'-help'],cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timeout=True
  k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr);cleanup=k.returncode
  try:code=p.wait(timeout=15)
  except subprocess.TimeoutExpired:pass
result={'exit':code,'seconds':time.monotonic()-start,'timeout':timeout,'budget_seconds':180,'cleanup':cleanup,'conversion_executed':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-5000:],flush=True)
if timeout or code:raise SystemExit('Converter help probe stopped; preserve logs')
