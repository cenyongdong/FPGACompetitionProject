"""One finite, pinned-host read-only identity/resource audit; no SDK/MMIO."""
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,sys,time
R=Path(__file__).resolve().parents[3]
E=R/'tools/pose-v1/evidence/hdmi-bringup-20261015-r1'
W=R/'.local/hdmi-bringup-20261015-r1'
E.mkdir(exist_ok=False);W.mkdir(exist_ok=False)
for name in ('PROJECT-PROGRESS.md','DIFFICULTIES.md','Done.md','REFERENCES.md','ARCHITECTURE-DISCUSSION-20261015.md'):
 p=E/'before'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/name,p)
shutil.copytree(R/'FPGA/hdmi_candidate',E/'before/FPGA/hdmi_candidate')
transport=R/'.local/shared-stability-transport-20261015-r2/secure_transport.py'
shutil.copyfile(transport,W/'secure_transport.py')
pre=(R/'tools/pose-v1/board_application_preflight.py').read_text(encoding='utf-8')
functions=pre[:pre.index('out=pathlib.Path(sys.argv[1])')]
expected=json.loads((R/'tools/pose-v1/evidence/hdmi-register-probe-20261015-r3/expected.json').read_text())
code=functions+'\nexpected='+repr(expected)+'\n'+'''
import os
boot=next(x for x in fat_files() if x['name']=='BOOT.BIN')
libs={n:digest('/usr/lib/aarch64-linux-gnu/'+n) for n in expected['libraries']}
assert boot['sha256']==expected['BOOT_sha256'],'BOOT identity changed; stop'
assert libs==expected['libraries'],'SDK identity changed; stop'
def read(p):
 try:return pathlib.Path(p).read_text().strip()
 except OSError:return None
processes=[]
for p in pathlib.Path('/proc').iterdir():
 if not p.name.isdecimal():continue
 item={'pid':int(p.name),'comm':read(p/'comm'),'device_fds':[]}
 try:files=list((p/'fd').iterdir())
 except OSError:continue
 for f in files:
  try:target=os.readlink(f)
  except OSError:continue
  if target.startswith(('/dev/mem','/dev/udma','/dev/u-dma','/dev/video','/dev/fb','/dev/dri')):
   item['device_fds'].append({'fd':f.name,'target':target})
 processes.append(item)
kernel=subprocess.check_output(['dmesg'])
print(json.dumps({'scope':'BOOT FAT16 block read + library hashes + proc/sysfs; no SDK/MMIO or writes',
 'boot':boot,'libraries':libs,'kernel_log_sha256':hashlib.sha256(kernel).hexdigest(),
 'fpga_state':read('/sys/class/fpga_manager/fpga0/state'),'boot_id':read('/proc/sys/kernel/random/boot_id'),
 'uname':subprocess.check_output(['uname','-a']).decode().strip(),'memory':read('/proc/meminfo'),
 'processes':processes,'device_owners':[p for p in processes if p['device_fds']],
 'note':'No Linux FD owner is not proof that PL scanout is stopped.'},indent=2))
'''
(E/'readonly-code.py').write_text(code,encoding='utf-8')
(E/'authorization.json').write_text(json.dumps({'user_authorized_board_validation':True,
 'persistent_BOOT_replacement':False,'old_DATA_investigation':False,
 'this_operation':'one read-only SSH audit','budget_seconds':20},indent=2)+'\n')
t=time.monotonic()
p=subprocess.run([sys.executable,str(W/'secure_transport.py'),'ssh','python3 -c '+shlex.quote(code),
 '--timeout','20','--log',str(E/'board-preflight.remote.txt')],capture_output=True,timeout=30)
(E/'board-preflight.stdout.txt').write_bytes(p.stdout);(E/'board-preflight.stderr.txt').write_bytes(p.stderr)
(E/'board-preflight-exit.json').write_text(json.dumps({'exit':p.returncode,'seconds':time.monotonic()-t,'transport_budget':20,'outer_budget':30})+'\n')
if p.returncode:raise SystemExit('Board preflight failed; preserve and stop without retry')
result=json.loads((E/'board-preflight.remote.txt').read_text())
(E/'board-preflight.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'BOOT_match':True,'SDK_libraries_match':len(result['libraries']),
 'fpga_state':result['fpga_state'],'device_owners':result['device_owners'],
 'process_count':len(result['processes']),'exit':p.returncode,'seconds':time.monotonic()-t}))
