"""Run a native isolated Vivado stage; observe slow jobs without killing them."""
from pathlib import Path
import argparse,json,subprocess,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-boot-witness-20261019-r23'
W=R/'.local/hdmi-boot-witness-20261019-r23'
V=Path('D:/vivado18.3/Vivado/2018.3/bin/vivado.bat')
def main():
 p=argparse.ArgumentParser();p.add_argument('stage');p.add_argument('--evidence',type=Path,default=E);p.add_argument('--work',type=Path,default=W);args=p.parse_args()
 evidence=args.evidence.resolve();work=args.work.resolve()
 script=evidence/(args.stage+'.tcl')
 if not script.is_file():raise FileNotFoundError(script)
 run=work/args.stage;run.mkdir(parents=True,exist_ok=False)
 command=[str(V),'-mode','batch','-nojournal','-log',str(evidence/(args.stage+'.vivado.log')),'-source',str(script)]
 start=time.monotonic()
 with (evidence/(args.stage+'.stdout.log')).open('xb') as so,(evidence/(args.stage+'.stderr.log')).open('xb') as se:
  proc=subprocess.Popen(command,cwd=run,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
  record=dict(stage=args.stage,pid=proc.pid,command=command,cwd=str(run),started_unix=time.time(),automatic_kill=False)
  (evidence/(args.stage+'-process.json')).write_text(json.dumps(record,indent=2))
  while proc.poll() is None:
   try:proc.wait(timeout=30)
   except subprocess.TimeoutExpired:print(json.dumps(dict(event='still_running',stage=args.stage,pid=proc.pid,elapsed=time.monotonic()-start)),flush=True)
 record.update(exit_code=proc.returncode,seconds=time.monotonic()-start)
 (evidence/(args.stage+'-execution.json')).write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
 raise SystemExit(proc.returncode)
if __name__=='__main__':main()
