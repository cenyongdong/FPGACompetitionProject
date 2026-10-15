"""One /proc and sysfs observation after the SDK register probe; no SDK use."""
from pathlib import Path
import json,shlex,subprocess,sys
R=Path(__file__).resolve().parents[2]
E=R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3'
T=R/'.local/hdmi-register-probe-20261015-r3/secure_transport.py'
code='''
from pathlib import Path
import json,os
def text(p):
 try:return Path(p).read_text().strip()
 except OSError:return None
processes=[]
for p in sorted(Path('/proc').iterdir()):
 if not p.name.isdecimal():continue
 item={'pid':int(p.name),'comm':text(p/'comm'),'relevant_fds':[]}
 try:files=list((p/'fd').iterdir())
 except OSError:continue
 for f in files:
  try:target=os.readlink(f)
  except OSError:continue
  if target.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri')):
   item['relevant_fds'].append({'fd':f.name,'target':target})
 processes.append(item)
assert len(processes)<1024,'Unexpected process scale; stop'
print(json.dumps({'scope':'proc/sysfs only, no SDK or device access','processes':processes,
 'fpga_state':text('/sys/class/fpga_manager/fpga0/state'),'boot_id':text('/proc/sys/kernel/random/boot_id'),
 'note':'No fd owner does not prove PL scanout stopped; hardware can continue without a Linux process.'},indent=2))
'''
assert not (E/'05-resource-owners.remote.txt').exists()
(E/'05-resource-owners-code.py').write_text(code,encoding='utf-8')
p=subprocess.run([sys.executable,str(T),'ssh','python3 -c '+shlex.quote(code),'--timeout','20','--log',str(E/'05-resource-owners.remote.txt')],capture_output=True,timeout=30)
(E/'05-resource-owners.stdout.txt').write_bytes(p.stdout)
(E/'05-resource-owners.stderr.txt').write_bytes(p.stderr)
(E/'05-resource-owners-exit.json').write_text(json.dumps({'exit':p.returncode,'timeout_seconds':20})+'\n',encoding='utf-8')
if p.returncode:raise SystemExit('Observation failed; do not repeat')
r=json.loads((E/'05-resource-owners.remote.txt').read_text())
print(json.dumps({'device_owners':[x for x in r['processes'] if x['relevant_fds']],
 'probe_processes':[x for x in r['processes'] if 'hdmi_readonly' in (x['comm'] or '')],
 'process_count':len(r['processes']),'fpga_state':r['fpga_state']}))
