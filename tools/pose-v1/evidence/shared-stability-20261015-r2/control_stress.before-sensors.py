"""Start/poll/stop only the explicitly budgeted, owned resident validation controller."""
from pathlib import Path
import hashlib,json,shlex,subprocess,sys
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
T=R/'.local/shared-stability-transport-20261015-r2/secure_transport.py'
remote='/tmp/wifi-pose-shared-stability-20261015-r2'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def call(mode,source,dest,log,timeout=30):
    args=[sys.executable,str(T),mode,source]
    if dest:args.append(dest)
    args+=['--timeout',str(timeout),'--log',str(E/log)]
    p=subprocess.run(args,capture_output=True)
    sys.stdout.buffer.write(p.stdout+p.stderr);sys.stdout.flush()
    if p.returncode:raise RuntimeError('Stress control failed; no retry')
action=sys.argv[1]
if action=='start':
    review=load(E/'short-reviewed.json');assert review['approved_to_start_stress']
    assert load(E/'basic-analysis.json')['status']=='passed'
    assert (E/'restart-authorization.json').exists()
    call('put',str(E/'short-reviewed.json'),remote+'/short-reviewed.json','10-short-review-transfer.txt')
    code="""from pathlib import Path
import json,subprocess,os,hashlib
r=Path(REMOTE);assert not (r/'run-stress').exists() and not (r/'stress-controller.json').exists()
assert (r/'run-basic/exit.txt').read_text().strip()=='0' and (r/'run-short/exit.txt').read_text().strip()=='0'
review=json.loads((r/'short-reviewed.json').read_text());assert review['approved_to_start_stress']
assert hashlib.sha256((r/'package.json').read_bytes()).hexdigest()==review['package_sha256']
cmd=['python3',str(r/'run_stage.py'),'--stage','stress']
with (r/'stress-controller.stdout.txt').open('xb') as out,(r/'stress-controller.stderr.txt').open('xb') as err:
 p=subprocess.Popen(cmd,cwd=r,stdout=out,stderr=err,start_new_session=True)
 stat=(Path('/proc')/str(p.pid)/'stat').read_text();start=stat[stat.rfind(')')+2:].split()[19]
 info=dict(pid=p.pid,pgid=os.getpgid(p.pid),start_ticks=start,command=cmd,budget_seconds=1800,max_frames=90000)
 assert info['pgid']==p.pid
 (r/'stress-controller.json').write_text(json.dumps(info,indent=2)+chr(10));print(json.dumps(info))
""".replace('REMOTE',repr(remote))
    call('ssh','python3 -c '+shlex.quote(code),None,'11-stress-start.txt')
elif action=='poll':
    log=sys.argv[2];assert log.startswith('poll-') and log.endswith('.txt')
    code="""from pathlib import Path
import json,os
r=Path(REMOTE);info=json.loads((r/'stress-controller.json').read_text());p=Path('/proc')/str(info['pid']);running=False
if (p/'stat').exists():
 s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split();running=f[19]==str(info['start_ticks']) and f[0]!='Z'
run=r/'run-stress';progress=run/'results/progress.json';exit_file=run/'exit.txt';res=run/'resources.jsonl'
sample=None
if res.exists():
 with res.open('rb') as f:
  f.seek(max(0,res.stat().st_size-16384));rows=f.read().splitlines()
 for line in reversed(rows):
  try:sample=json.loads(line);break
  except ValueError:pass
result=dict(controller_running=running,progress=json.loads(progress.read_text()) if progress.exists() else None,
 exit=int(exit_file.read_text()) if exit_file.exists() else None,evidence_complete=(run/'evidence-files.json').exists(),
 latest_resource=sample)
if (run/'results/failure.json').exists():result['failure']=json.loads((run/'results/failure.json').read_text())
if (run/'monitor-failure.json').exists():result['monitor_failure']=json.loads((run/'monitor-failure.json').read_text())
print(json.dumps(result))
""".replace('REMOTE',repr(remote))
    call('ssh','python3 -c '+shlex.quote(code),None,log)
elif action=='stop':
    code="""from pathlib import Path
import json,os,signal,time
r=Path(REMOTE);info=json.loads((r/'stress-controller.json').read_text());pid=info['pid'];p=Path('/proc')/str(pid)
def controller_alive():
 if not (p/'stat').exists():return False
 s=(p/'stat').read_text();f=s[s.rfind(')')+2:].split();return f[19]==str(info['start_ticks']) and f[0]!='Z'
if controller_alive():
 assert os.getpgid(pid)==pid;os.killpg(pid,signal.SIGTERM)
 for i in range(20):
  if not controller_alive():break
  time.sleep(.5)
 if controller_alive():os.killpg(pid,signal.SIGKILL)
childfile=r/'run-stress/child.pid'
if childfile.exists():
 child=int(childfile.read_text());cp=Path('/proc')/str(child)
 if (cp/'cmdline').exists() and (cp/'cmdline').read_bytes().split(bytes([0]))[0]==str(r/'pose_shared_resident').encode():
  assert os.getpgid(child)==child;os.killpg(child,signal.SIGTERM);time.sleep(5)
  if (cp/'cmdline').exists() and (cp/'cmdline').read_bytes().split(bytes([0]))[0]==str(r/'pose_shared_resident').encode():os.killpg(child,signal.SIGKILL)
print('Owned stress controller/child stop completed; review evidence before further load')
""".replace('REMOTE',repr(remote))
    call('ssh','python3 -c '+shlex.quote(code),None,'stop-requested.txt',40)
else:raise RuntimeError('Unsupported control action')
