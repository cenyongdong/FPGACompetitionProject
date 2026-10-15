"""Fresh finite SDK read-only probe; no writes, frame allocation or DMA start."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-bringup-20261015-r1'
W=R/'.local/hdmi-bringup-20261015-r1'
P=R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3'
REMOTE='/tmp/hdmi-bringup-20261015-r1'
preflight=json.loads((E/'board-preflight.json').read_text())
assert not preflight['device_owners'] and preflight['fpga_state']=='operating'
expected=json.loads((P/'expected.json').read_text())
binary=P/'hdmi_readonly_probe'
assert hashlib.sha256(binary.read_bytes()).hexdigest()==expected['binary_sha256']
transport=W/'secure_transport.py'
src=transport.read_text(encoding='utf-8')
assert "REMOTE = '/tmp/wifi-pose-shared-stability-20261015-r2/'" in src
transport.write_text(src.replace("REMOTE = '/tmp/wifi-pose-shared-stability-20261015-r2/'","REMOTE = '"+REMOTE+"/'"),encoding='utf-8',newline='\n')
steps=[]
def call(name,mode,source,dest=None):
 args=[sys.executable,str(transport),mode,source]
 if dest:args.append(dest)
 args+=['--timeout','20','--log',str(E/(name+'.remote.txt'))]
 t=time.monotonic();p=subprocess.run(args,capture_output=True,timeout=30)
 (E/(name+'.stdout.txt')).write_bytes(p.stdout);(E/(name+'.stderr.txt')).write_bytes(p.stderr)
 steps.append({'stage':name,'exit':p.returncode,'seconds':time.monotonic()-t,'transport_budget':20})
 (E/'register-transport.json').write_text(json.dumps(steps,indent=2)+'\n')
 if p.returncode:raise SystemExit(name+' failed; stop without retry')
call('01-fresh-directory','ssh','mkdir -- '+REMOTE)
call('02-probe-transfer','put',str(binary),REMOTE+'/hdmi_readonly_probe')
driver=(P/'board-driver.py').read_text(encoding='utf-8')
old="remote='/tmp/hdmi-register-probe-20261015-r3'"
assert driver.count(old)==1
driver=driver.replace(old,'remote='+repr(REMOTE))
(E/'readonly-sdk-driver.py').write_text(driver,encoding='utf-8')
call('03-sdk-read-once','ssh','python3 -c '+shlex.quote(driver))
result=json.loads((E/'03-sdk-read-once.remote.txt').read_text())
(E/'readonly-sdk-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'exit':result['probe_exit'],'seconds':result['elapsed_seconds'],
 'budget':result['budget_seconds'],'kernel_unchanged':result['kernel_log_unchanged'],
 'FPGA':result['fpga_state'],'child_reaped':result['child_reaped'],
 'probe_stdout':result['stdout']},ensure_ascii=False))
