"""Native RTL checks for startup history and the existing observer protocol."""
from pathlib import Path
import argparse,json,subprocess,time
R=Path(__file__).resolve().parents[3]
E_BASE=R/'tools/pose-v1/evidence/hdmi-boot-witness-20261019-r23'
W_BASE=R/'.local/hdmi-boot-witness-20261019-r23'
V=Path('D:/vivado18.3/Vivado/2018.3/bin')

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,default=1);parser.add_argument('--only-boot',action='store_true');args=parser.parse_args()
 E=E_BASE/('sim-r'+str(args.attempt));W=W_BASE/('sim-r'+str(args.attempt))
 E.mkdir(parents=True,exist_ok=True);W.mkdir(parents=True,exist_ok=True)
 sources=[R/'.local/hdmi-live-20261018-r9/reference/rtl/utils/mna_itf.sv',
          R/'FPGA/hdmi_candidate/diagnostics/ai_boot_witness.sv',
          R/'FPGA/hdmi_candidate/diagnostics/ai_read_monitor.sv',
          R/'FPGA/hdmi_candidate/sim/tb_ai_boot_witness.sv',
          R/'FPGA/hdmi_candidate/sim/tb_ai_read_monitor.sv']
 for p in sources:
  if not p.is_file():raise FileNotFoundError(p)
 (W/'run.tcl').write_text('run all\nquit\n',encoding='ascii')
 stages=[('compile',[str(V/'xvlog.bat'),'--sv',*[str(p) for p in sources]])]
 for top in (('tb_ai_boot_witness',) if args.only_boot else ('tb_ai_boot_witness','tb_ai_read_monitor')):
  snapshot=top+'_unit'
  stages.extend([(top+'-elaborate',[str(V/'xelab.bat'),top,'--timescale','1ns/1ps','--snapshot',snapshot]),
                 (top+'-simulate',[str(V/'xsim.bat'),snapshot,'--tclbatch','run.tcl'])])
 results=[]
 for name,argv in stages:
  start=time.monotonic()
  with (E/(name+'.stdout.log')).open('xb') as out,(E/(name+'.stderr.log')).open('xb') as err:
   p=subprocess.Popen(argv,cwd=W,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
   (E/'sim-process.json').write_text(json.dumps(dict(pid=p.pid,stage=name,argv=argv,started_unix=time.time()),indent=2))
   while p.poll() is None:
    try:p.wait(timeout=30)
    except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',stage=name,pid=p.pid,elapsed=time.monotonic()-start)),flush=True)
  row=dict(stage=name,exit_code=p.returncode,seconds=time.monotonic()-start,argv=argv)
  results.append(row);(E/'sim-execution.json').write_text(json.dumps(results,indent=2));print(json.dumps(row),flush=True)
  if p.returncode:raise RuntimeError(name+' native failure; inspect saved logs')
 expected={'tb_ai_boot_witness-simulate':['AI_BOOT_WITNESS_PASS','BOOT_WITNESS_RESET_WITH_STOPPED_HP_CLOCK_PASS'],
           'tb_ai_read_monitor-simulate':['AI_READ_MONITOR_PASS','AI_READ_MONITOR_EXPECTED_TIMEOUT']}
 for name,markers in expected.items():
  if args.only_boot and name.startswith('tb_ai_read_monitor'):continue
  output=(E/(name+'.stdout.log')).read_text(errors='replace')
  if any(x not in output for x in markers) or 'Fatal:' in output:raise RuntimeError('Simulation did not complete: '+name)
 tests=['history before ARM','reset witness with stopped HP clock','history survives local reset','held CSR snapshot']
 if not args.only_boot:tests.append('existing observer regression')
 result=dict(passed=True,tests=tests,board_access=False)
 (E/'sim-result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
if __name__=='__main__':main()
