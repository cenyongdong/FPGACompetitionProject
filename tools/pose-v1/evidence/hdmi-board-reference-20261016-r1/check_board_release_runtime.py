"""One pinned-host bounded read-only board audit; preserve every result."""
from pathlib import Path
import json, shlex, subprocess, sys, time, shutil
R=Path(__file__).resolve().parents[3];NAME='hdmi-board-reference-20261016-r1'
E=R/'tools/pose-v1/evidence'/NAME;W=R/'.local'/NAME
pre=(R/'tools/pose-v1/board_application_preflight.py').read_text(encoding='utf-8')
expected=json.loads((R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())
code=pre[:pre.index('out=pathlib.Path(sys.argv[1])')]+'\nexpected='+repr(expected)+'\n'+'''
import os, glob
def read(p):
 try:return pathlib.Path(p).read_text().strip()
 except (OSError,UnicodeError):return None
boot=next(x for x in fat_files() if x['name']=='BOOT.BIN')
libs={n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']}
assert boot['sha256']==expected['BOOT_sha256'],'BOOT identity changed; stop'
assert libs==expected['libraries'],'SDK identity changed; stop'
processes=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 item={'pid':int(p.name),'comm':read(p/'comm'),'device_fds':[]}
 try:files=list((p/'fd').iterdir())
 except OSError:continue
 for f in files:
  try:target=os.readlink(f)
  except OSError:continue
  if target.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri','/dev/xdma')):item['device_fds'].append({'fd':f.name,'target':target})
 processes.append(item)
sysfs={}
for root in ['/sys/class/fpga_manager','/sys/class/fpga_bridge','/sys/class/fpga_region']:
 sysfs[root]=[]
 for p in pathlib.Path(root).glob('*'):
  sysfs[root].append({'name':p.name,'path':str(p.resolve()),'attrs':{n:read(p/n) for n in ['name','state','status','flags','firmware','enable']},'entries':[x.name for x in p.iterdir()]})
dt=[]
for p in pathlib.Path('/sys/firmware/devicetree/base').rglob('compatible'):
 b=p.read_bytes()
 if any(k in b.lower() for k in [b'fpga',b'devcfg',b'decouple',b'bridge',b'zynq']):
  dt.append({'path':str(p.parent),'compatible':b.decode(errors='replace').split(chr(0)),'status':read(p.parent/'status')})
kernel=subprocess.check_output(['dmesg']).decode(errors='replace')
result={'scope':'Read-only boot block hashes, libraries, proc/sysfs/device-tree; no MMIO/SDK/configuration writes',
 'BOOT':boot,'libraries':libs,'boot_id':read('/proc/sys/kernel/random/boot_id'),
 'uname':subprocess.check_output(['uname','-a']).decode().strip(),
 'fpga_state':read('/sys/class/fpga_manager/fpga0/state'),'processes':processes,
 'device_owners':[p for p in processes if p['device_fds']], 'fpga_sysfs':sysfs,'device_tree':dt,
 'kernel_log':kernel,'kernel_sha256':hashlib.sha256(kernel.encode()).hexdigest(),
 'memory':read('/proc/meminfo'),'mounts':read('/proc/mounts'),
 'devcfg_devices':glob.glob('/dev/*devcfg*'),'note':'No FD owner does not prove AXI drain.'}
print(json.dumps(result,indent=2))
'''
(E/'board-readonly-code.py').write_text(code,encoding='utf-8')
assert not (E/'board-audit-exit.json').exists()
t=time.monotonic()
p=subprocess.run([sys.executable,str(W/'secure_transport.py'),'ssh','python3 -c '+shlex.quote(code),
 '--timeout','30','--log',str(E/'board-audit.remote.txt')],capture_output=True,timeout=40)
(E/'board-audit.stdout.txt').write_bytes(p.stdout);(E/'board-audit.stderr.txt').write_bytes(p.stderr)
(E/'board-audit-exit.json').write_text(json.dumps({'exit':p.returncode,'seconds':time.monotonic()-t,'transport_budget_seconds':30,'outer_budget_seconds':40})+'\n')
shutil.copyfile(Path(__file__),E/Path(__file__).name)
if p.returncode:raise SystemExit('Read-only audit failed; stop dependent board operations')
result=json.loads((E/'board-audit.remote.txt').read_text(encoding='utf-8'))
(E/'board-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['BOOT','fpga_state','device_owners','fpga_sysfs','devcfg_devices']},indent=2))
