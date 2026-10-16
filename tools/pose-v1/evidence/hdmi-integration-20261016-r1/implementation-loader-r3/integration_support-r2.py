"""One owned EDA job with recorded, bounded progress-based timeout decisions."""
from pathlib import Path
import json,os,subprocess,time,ctypes
R=Path('D:\\FPGACompetitionProject');E=R/'tools/pose-v1/evidence/hdmi-integration-20261016-r1';W=R/'.local/hdmi-integration-20261016-r1'
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
class Memory(ctypes.Structure):
 _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ['totalPhys','availPhys','totalPage','availPage','totalVirt','availVirt','availExt']]
def memory():
 m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
 return {'available_MB':m.availPhys//1048576,'load_percent':m.load,'available_commit_MB':m.availPage//1048576}
def stage(name,tcl,ceiling=1800,run_names=None):
 out=E/name;work=W/name;out.mkdir(exist_ok=False);work.mkdir(exist_ok=False)
 tcl=tcl.replace('@@OUT@@',out.as_posix()).replace('@@REF@@',(W/'reference').as_posix()).replace('@@WORK@@',work.as_posix())
 (out/'stage.tcl').write_text(tcl,encoding='utf-8');(work/'stage.tcl').write_text(tcl,encoding='utf-8')
 env=os.environ.copy();env.update({'PROCESSOR_ARCHITECTURE':'AMD64','XILINX_VIVADO':'D:/vivado18.3/Vivado/2018.3','JFM_PATH':str(W/'reference'),'FMSH_PROCISE_PATH':'C:/FudanMicro/Procise'})
 for n in list(env):
  if n.startswith('RDI_'):env.pop(n)
 args=['D:/vivado18.3/Vivado/2018.3/bin/vivado.bat','-mode','batch','-nojournal','-log',str(out/'vivado.log'),'-source',str(work/'stage.tcl')]
 start=time.monotonic();budget=180;last_size=0;decisions=[];stop=False
 with (out/'stdout.txt').open('wb') as stdout,(out/'stderr.txt').open('wb') as stderr:
  p=subprocess.Popen(args,cwd=work,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)
  dump(out/'owned-process.json',{'pid':p.pid,'initial_budget':180,'ceiling':ceiling,'work':str(work),'resource_at_start':memory()})
  while p.poll() is None:
   elapsed=time.monotonic()-start
   if elapsed>=budget:
    run_root=W/'reference/fpai_demo_vivado.runs'
    roots=[run_root] if run_names is None else [run_root/n for n in run_names]
    logs=[p for root in roots for p in root.rglob('*.log')]+[out/'stdout.txt',out/'vivado.log']
    logs=[f for f in logs if f.exists()];size=sum(f.stat().st_size for f in logs);age=min((time.time()-f.stat().st_mtime for f in logs),default=1e9)
    tails=[f.read_text(encoding='utf-8',errors='replace')[-24000:] for f in logs]
    error=any('ERROR:' in text for text in tails);mem=memory()
    extend=budget<ceiling and size>last_size and age<180 and not error and mem['available_MB']>350 and mem['available_commit_MB']>800
    item={'elapsed':elapsed,'previous_budget':budget,'new_budget':min(budget+180,ceiling) if extend else budget,
      'log_bytes':size,'youngest_log_age_seconds':age,'error_seen':error,'memory':mem,
      'action':'continue original owned process' if extend else 'stop and preserve'}
    decisions.append(item);dump(out/'timeout-decisions.json',decisions);print(json.dumps(item),flush=True)
    if extend:budget=min(budget+180,ceiling);last_size=size
    else:
     stop=True;k=subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=20)
     (out/'cleanup.txt').write_bytes(k.stdout+k.stderr)
     try:p.wait(timeout=20)
     except subprocess.TimeoutExpired:pass
     break
   time.sleep(1)
 result={'exit':p.poll(),'seconds':time.monotonic()-start,'initial_budget_seconds':180,'final_budget_seconds':budget,
  'ceiling_seconds':ceiling,'stopped_by_monitor':stop,'decisions':decisions,'final_memory':memory()}
 dump(out/'execution.json',result);print(json.dumps(result),flush=True)
 print((out/'stdout.txt').read_text(encoding='utf-8',errors='replace')[-1800:].encode('ascii',errors='backslashreplace').decode('ascii'),flush=True)
 if p.poll()!=0 or stop:raise SystemExit('Stage failed/stopped; preserve evidence, diagnose before dependent operations')
 return out
