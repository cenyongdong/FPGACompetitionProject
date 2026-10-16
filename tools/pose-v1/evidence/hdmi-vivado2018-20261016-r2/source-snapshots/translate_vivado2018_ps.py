"""Use installed converter on the new real PS EDIF; preserve original and diff."""
from pathlib import Path
import difflib,json,os,shutil,subprocess,time,hashlib
R=Path(__file__).resolve().parents[3];E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/translate-ps';W=R/'.local/hdmi-vivado2018-20261016-r2/translate-ps'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
src=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r2/actual-ps-synth/actual_ps.edf'
assert json.loads((src.parent/'connected-contract-review.json').read_text(encoding='utf-8'))['gate_pass']
shutil.copyfile(src,W/src.name);dest=W/'converted';dest.mkdir()
root=Path('C:/FudanMicro/Procise');env=os.environ.copy()
env.update(APP_DIR=str(root),ICTIME_HOME=str(root),FMSH_DB=str(root/'db'),TCL_LIBRARY=str(root/'tcl8.4'))
env['PATH']=str(root/'dll')+';'+str(root/'bin')+';'+env['PATH']
args=[str(root/'bin/translate_file.exe'),'-to_procise','-source',str(W/src.name),'-out_dir',str(dest)]
start=time.monotonic();timeout=False;code=None
with (E/'stdout.txt').open('wb') as out,(E/'stderr.txt').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,env=env,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 try:code=p.wait(timeout=180)
 except subprocess.TimeoutExpired:
  timeout=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
  (E/'cleanup.txt').write_bytes(k.stdout+k.stderr)
  try:code=p.wait(timeout=15)
  except subprocess.TimeoutExpired:pass
result={'exit':code,'seconds':time.monotonic()-start,'timeout':timeout,'budget_seconds':180,'input_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'implementation_or_binding_pass':False}
(E/'execution.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
shutil.copytree(dest,E/'converted')
print(json.dumps(result),flush=True)
print((E/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-2000:],flush=True)
if code or timeout:raise SystemExit('Conversion failed; preserve and stop')
files=list(dest.glob('*'));assert len(files)==1,files
before=src.read_text(encoding='utf-8');after=files[0].read_text(encoding='utf-8')
(E/'conversion.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='Vivado_actual_ps.edf',tofile=files[0].name)),encoding='utf-8')
print('diff',str(E/'conversion.diff'),flush=True)
