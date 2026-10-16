"""Bounded 2018.3 subprocess stages in fresh evidence/work directories."""
from pathlib import Path
import hashlib, json, os, shutil, subprocess, time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-vivado2018-20261016-r1'
W=R/'.local/hdmi-vivado2018-20261016-r1'
INSTALLED=Path('D:/vivado18.3/Vivado/2018.3')
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def stage(name,script,budget=60,tool=INSTALLED,env_extra=None,inputs=None):
 out=E/name;work=W/name;out.mkdir(exist_ok=False);work.mkdir(exist_ok=False)
 if inputs:
  manifest=[]
  for source in inputs:
   source=Path(source);target=work/source.name
   shutil.copyfile(source,target)
   identity=sha(source);assert sha(target)==identity
   manifest.append({'source':str(source),'name':source.name,'sha256':identity})
  dump(out/'sources.json',manifest)
 script=script.replace('@@OUT@@',out.as_posix()).replace('@@WORK@@',work.as_posix())
 (work/'stage.tcl').write_text(script,encoding='utf-8');shutil.copyfile(work/'stage.tcl',out/'stage.tcl')
 env=os.environ.copy();env['PROCESSOR_ARCHITECTURE']='AMD64'
 env['XILINX_VIVADO']=tool.as_posix()
 for n in list(env):
  if n.startswith('RDI_'):env.pop(n)
 if env_extra:env.update(env_extra)
 args=[str(tool/'bin/vivado.bat'),'-mode','batch','-nojournal','-log',str(out/'vivado.log'),'-source',str(work/'stage.tcl')]
 start=time.monotonic();timeout=False;code=None;cleanup=None;driver_error=None
 with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
  p=subprocess.Popen(args,cwd=work,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  try:code=p.wait(timeout=budget)
  except subprocess.TimeoutExpired:
   timeout=True
   try:
    clean=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=15)
    (out/'cleanup.txt').write_bytes(clean.stdout+clean.stderr)
    cleanup={'return_code':clean.returncode,'pid':p.pid}
    try:code=p.wait(timeout=15)
    except subprocess.TimeoutExpired:driver_error='Cleanup wait exceeded 15 seconds; process ownership review required'
   except Exception as ex:
    driver_error=type(ex).__name__+': '+str(ex)
 result={'exit':code,'seconds':time.monotonic()-start,'budget_seconds':budget,'timeout':timeout,
         'tool_root':str(tool),'work':str(work),'board_operation':False,
         'cleanup':cleanup,'driver_error':driver_error}
 dump(out/'execution.json',result)
 print(json.dumps(result),flush=True)
 print((out/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-1500:],flush=True)
 if code or timeout:raise SystemExit('Stage failed; evidence preserved, no automatic retry')
 return out,work
