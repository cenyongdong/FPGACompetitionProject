"""Final read-only identity/process audit after archive return. No device initialization."""
from pathlib import Path
import json,subprocess,sys
E=Path(__file__).resolve().parent;R=E.parents[3]
T=R/'.local/shared-stability-transport-20261015-r2/secure_transport.py'
B='/tmp/wifi-pose-shared-stability-20261015-r2'
assert (E/'archive-return-recovery.json').exists()
def call(mode,source,destination,log,timeout=30):
 args=[sys.executable,str(T),mode,source]
 if destination:args.append(str(destination))
 args+=['--timeout',str(timeout),'--log',str(E/(log+'.txt'))]
 p=subprocess.run(args,capture_output=True)
 if p.returncode:
  (E/(log+'-error.txt')).write_bytes(p.stdout+p.stderr)
  raise RuntimeError(log+' failed; preserve and stop')
 return p.stdout
call('ssh','cd '+B+' && python3 board_application_preflight.py final-preflight.json',None,'17-final-preflight',60)
call('get',B+'/final-preflight.json',E/'final-preflight.json','18-final-preflight-return')
kernel=call('ssh','dmesg',None,'19-final-dmesg')
p=json.loads((E/'final-preflight.json').read_text());previous=json.loads((E/'returned-stress/run-stress/post-preflight.json').read_text())
for key in ('boot_files','libraries','SDK_packages','fpga_state'):assert p[key]==previous[key],key
assert p['fpga_state']=='operating'
assert kernel==(E/'returned-stress/run-stress/after.dmesg.txt').read_bytes()
processes=p['processes'];assert 'pose_shared_' not in processes
assert 'run_stage.py' not in processes and 'tarfile' not in processes
report=dict(passed=True,no_inference_controller_or_archive_process_remains=True,SDK_BOOT_unchanged=True,
 kernel_unchanged=True,fpga_state=p['fpga_state'],inference_restarted=False,
 connections='Finite SSH/scp calls completed; no polling service or listener remains',
 unrelated_user_sessions='Existing user SSH/Moba monitoring left untouched')
(E/'final-cleanup-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
