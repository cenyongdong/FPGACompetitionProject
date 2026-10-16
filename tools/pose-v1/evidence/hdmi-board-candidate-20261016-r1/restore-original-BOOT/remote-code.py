
import pathlib,os,json,hashlib,subprocess,time,stat
root=pathlib.Path('/tmp/hdmi-board-candidate-20261016-r1');mnt=root/'boot-mount';pkg=root/'package';meta=root/'metadata'
original='ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef';candidate='22035d99f2dacdcb1817a0c08ae8b04c3b024e51bf2f1b522f0fcb9baf252135';uenv='a13c985eb5031d75ec7069333897cae38944ba5fbadd509828b63e6a48408560';old_boot_id='8974fbf7-cbe9-4fc9-954d-4682c45b045f'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def run(args):
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=20)
 assert p.returncode==0,repr(args)+': '+p.stdout.decode(errors='replace')
def mounts():return [line.split() for line in pathlib.Path('/proc/mounts').read_text().splitlines()]
def mounted():return any(v[1]==str(mnt) for v in mounts())
def mount(mode):
 assert stat.S_ISBLK(os.stat('/dev/mmcblk0p1').st_mode)
 assert not any(v[0]=='/dev/mmcblk0p1' for v in mounts()),'Boot partition unexpectedly mounted'
 run(['/usr/bin/mount','-t','vfat','-o',mode+',nosuid,nodev,noexec','/dev/mmcblk0p1',str(mnt)])
 rows=[v for v in mounts() if v[1]==str(mnt)]
 assert len(rows)==1 and rows[0][0]=='/dev/mmcblk0p1' and rows[0][2]=='vfat'
 assert mode in rows[0][3].split(',')
def unmount():
 if mounted():run(['/usr/bin/umount',str(mnt)])
 assert not mounted()
def files():
 return {p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in mnt.iterdir() if p.is_file()}
def unique(name):
 rows=[p for p in mnt.iterdir() if p.name.casefold()==name.casefold()]
 assert len(rows)==1 and rows[0].is_file(),name
 return rows[0]
def check_others(before,after,boot_name):
 assert set(before)==set(after),'Boot directory entries changed'
 assert all(before[n]==after[n] for n in before if n!=boot_name),'Non-BOOT startup file changed'
def save(name,data):
 p=meta/name
 with p.open('x',encoding='utf-8') as f:json.dump(data,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def replace_boot(source,expected_before,expected_after,record):
 assert digest(source)==expected_after
 mount('rw')
 try:
  before=files();boot=unique('boot.bin');assert digest(boot)==expected_before
  assert digest(unique('uenv.txt'))==uenv
  baseline=json.loads((meta/'prepare.json').read_text())['startup_files']
  check_others(baseline,before,boot.name)
  temp=mnt/'HDMIR5.NEW';assert not temp.exists()
  with temp.open('xb') as f:
   with source.open('rb') as src:
    for block in iter(lambda:src.read(1048576),b''):f.write(block)
   f.flush();os.fsync(f.fileno())
  assert digest(temp)==expected_after
  os.replace(temp,boot);os.sync()
  after=files();assert digest(boot)==expected_after
  check_others(before,after,boot.name)
  result={'BOOT_sha256':expected_after,'BOOT_name':boot.name,'other_startup_files_unchanged':True,
          'startup_files':after,'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
  save(record,result)
 finally:unmount()
 os.sync()
 return result

current=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert current!=old_boot_id,'Candidate startup not observed'
print(json.dumps(replace_boot(pkg/'BOOT-original.readback.bin',candidate,original,'restore.json'),indent=2))
