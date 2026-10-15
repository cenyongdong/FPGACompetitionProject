"""Compare exact kernel bytes using the controller's original capture mechanism."""
from pathlib import Path
import json,shlex,subprocess,sys
E=Path(__file__).resolve().parent;R=E.parents[3]
T=R/'.local/shared-stability-transport-20261015-r2/secure_transport.py'
B='/tmp/wifi-pose-shared-stability-20261015-r2'
def call(mode,source,destination,log):
 args=[sys.executable,str(T),mode,source]
 if destination:args.append(str(destination))
 args+=['--timeout','30','--log',str(E/(log+'.txt'))]
 p=subprocess.run(args,capture_output=True)
 if p.returncode:raise RuntimeError(log+' failed; preserve and stop')
 return p.stdout
code="from pathlib import Path; import subprocess; p=Path("+repr(B+'/final-dmesg-python.txt')+"); assert not p.exists(); p.write_bytes(subprocess.check_output(['dmesg']))"
call('ssh','python3 -c '+shlex.quote(code),None,'21-final-dmesg-same-capture')
call('get',B+'/final-dmesg-python.txt',E/'final-dmesg-python.txt','22-final-dmesg-file-return')
raw=(E/'final-dmesg-python.txt').read_bytes();original=(E/'returned-stress/run-stress/after.dmesg.txt').read_bytes()
assert raw==original,'Actual same-capture kernel bytes changed; stop'
display=(E/'19-final-dmesg.txt').read_bytes()
assert display.replace(b'\\xc2\\xa9',b'\xc2\xa9')==raw,'Unexplained diagnostic display differences'
p=json.loads((E/'final-preflight.json').read_text());previous=json.loads((E/'returned-stress/run-stress/post-preflight.json').read_text())
for key in ('boot_files','libraries','SDK_packages','fpga_state'):assert p[key]==previous[key],key
assert p['fpga_state']=='operating'
assert all(v not in p['processes'] for v in ('pose_shared_','run_stage.py','tarfile'))
report=dict(passed=True,no_inference_controller_or_archive_process_remains=True,SDK_BOOT_unchanged=True,
 kernel_unchanged=True,kernel_comparison='Complete bytes equal; exact original subprocess.check_output capture',
 prior_audit_assertion='Direct SSH shell dmesg escaped the existing copyright UTF-8 bytes as literal \\xc2\\xa9; original Python capture did not. First assertion preserved; no new kernel message.',
 fpga_state=p['fpga_state'],inference_restarted=False,
 connections='Finite SSH/scp calls completed; no polling service or listener remains',unrelated_user_sessions='Existing user SSH/Moba monitoring left untouched')
(E/'final-cleanup-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2))
