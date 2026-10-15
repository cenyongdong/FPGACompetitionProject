
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
