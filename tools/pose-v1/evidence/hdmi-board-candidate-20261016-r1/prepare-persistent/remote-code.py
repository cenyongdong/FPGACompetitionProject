
import pathlib,os,json,hashlib,subprocess,time,stat
root=pathlib.Path('/root/hdmi-board-candidate-20261016-r1');mnt=root/'boot-mount';pkg=root/'package';meta=root/'metadata'
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

assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='ab6d59c6-4921-4733-b04b-a0c4154069ae'
assert not root.exists(),'Fresh persistent directory required'
root.mkdir(mode=0o700);pkg.mkdir();mnt.mkdir();meta.mkdir()
save('prepare.json',{'startup_files': {'ai7030_top_disable_icap.bit': {'bytes': 5980604, 'sha256': '85fb81d09a0dcb51cb9d5d347c01de43eccec14c6eb9a87e1876105b3efc4b81'}, 'bl31.elf': {'bytes': 610824, 'sha256': 'fdcf0af48a7f9716f73a477c3cc1b4cd90c914fe0e5ad7acc5ab282660802303'}, 'BOOT.bin': {'bytes': 7023552, 'sha256': 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'}, 'fmqlmp-verify.dtb': {'bytes': 15996, 'sha256': '4e690cf065424e28ad7e39e0dc87a72f4c593f5bd4d99c11f7c4e892feee3038'}, 'Image': {'bytes': 13158408, 'sha256': 'ee88eae627df17fdf615b44cb9fc5a7a7a37d2baaa3f21e90d613f48bedf0929'}, 'u-boot': {'bytes': 6579840, 'sha256': 'c4570e3e51128211905bdf20c7b7e0ea9cb7ca1492652a070ebdd985bc213e97'}, 'uEnv.txt': {'bytes': 1499, 'sha256': 'a13c985eb5031d75ec7069333897cae38944ba5fbadd509828b63e6a48408560'}, 'ai7030_top.bit': {'bytes': 5980020, 'sha256': '1405d7f1cb992d8f9c78e7b4bbe756faa96eeecb2ff4bdd0d253e92b191e2575'}, 'FSBL251210_ddr400_demo.out': {'bytes': 1385156, 'sha256': '5501c470e07537a8fb369ae40641c20c16ab403fad558e65e0a4bbf380f2396f'}}, 'backup_sha256': 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef', 'uEnv_sha256': 'a13c985eb5031d75ec7069333897cae38944ba5fbadd509828b63e6a48408560', 'free_FAT_bytes': 997064704, 'BOOT_name': 'BOOT.bin', 'BOOT_changed': False, 'boot_id': '8974fbf7-cbe9-4fc9-954d-4682c45b045f'})
print(json.dumps({'persistent_staging':str(root),'mounted':False,'BOOT_changed_by_this_step':False}))
