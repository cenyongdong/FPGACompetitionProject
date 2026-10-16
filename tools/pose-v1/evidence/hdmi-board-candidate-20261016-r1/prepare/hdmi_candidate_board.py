"""Finite stages for the explicitly approved r5 temporary BOOT test."""
from pathlib import Path
import hashlib
import json
import shlex
import subprocess
import sys
import time
import shutil

R = Path(__file__).resolve().parents[3]
E = R / 'tools/pose-v1/evidence/hdmi-board-candidate-20261016-r1'
W = R / '.local/hdmi-board-candidate-20261016-r1'
C = R / 'tools/pose-v1/evidence/hdmi-integration-20261016-r1'
REMOTE = '/tmp/hdmi-board-candidate-20261016-r1'
ORIGINAL = 'ff350477e624c50d2f8180fb4b9130ec7688fbc7ca553412ed7c3dd2a68b31ef'
CANDIDATE = '22035d99f2dacdcb1817a0c08ae8b04c3b024e51bf2f1b522f0fcb9baf252135'
UENV = 'a13c985eb5031d75ec7069333897cae38944ba5fbadd509828b63e6a48408560'
OLD_BOOT_ID = '8974fbf7-cbe9-4fc9-954d-4682c45b045f'
auth = json.loads((E / 'authorization.json').read_text())
assert auth['candidate_startup_reboot_limit'] == auth['original_fallback_reboot_limit'] == 1


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def execute(stage, code, budget=60):
    out = E / stage
    out.mkdir(exist_ok=False)
    (out / 'remote-code.py').write_text(code, encoding='utf-8')
    start = time.monotonic()
    proc = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'ssh',
                           'python3 -c ' + shlex.quote(code), '--timeout', str(budget),
                           '--log', str(out / 'remote.txt')], capture_output=True, timeout=budget + 10)
    (out / 'stdout.txt').write_bytes(proc.stdout)
    (out / 'stderr.txt').write_bytes(proc.stderr)
    dump(out / 'execution.json', {'exit': proc.returncode, 'seconds': time.monotonic() - start,
                                 'transport_budget': budget, 'outer_budget': budget + 10})
    shutil.copyfile(Path(__file__), out / Path(__file__).name)
    assert proc.returncode == 0, f'{stage} failed: preserve; do not repeat affected stage'
    data = json.loads((out / 'remote.txt').read_text(encoding='utf-8'))
    dump(out / 'result.json', data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return data


COMMON = r'''
import pathlib,os,json,hashlib,subprocess,time,stat
root=pathlib.Path('@@REMOTE@@');mnt=root/'boot-mount';pkg=root/'package';meta=root/'metadata'
original='@@ORIGINAL@@';candidate='@@CANDIDATE@@';uenv='@@UENV@@';old_boot_id='@@BOOTID@@'
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
'''
for token, value in [('REMOTE', REMOTE), ('ORIGINAL', ORIGINAL), ('CANDIDATE', CANDIDATE),
                     ('UENV', UENV), ('BOOTID', OLD_BOOT_ID)]:
    COMMON = COMMON.replace('@@' + token + '@@', value)

stage = sys.argv[1]
if stage == 'prepare':
    data = execute('prepare', COMMON + r'''
assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()==old_boot_id
assert not root.exists(),'Fresh remote package required'
root.mkdir(mode=0o700);pkg.mkdir();mnt.mkdir();meta.mkdir()
mount('ro')
try:
 before=files();boot=unique('boot.bin');env=unique('uenv.txt')
 assert digest(boot)==original and digest(env)==uenv
 free=os.statvfs(str(mnt));free_bytes=free.f_bavail*free.f_frsize
 assert free_bytes>3*boot.stat().st_size+1048576
 backup=pkg/'BOOT-original.readback.bin'
 with backup.open('xb') as f:f.write(boot.read_bytes());f.flush();os.fsync(f.fileno())
 assert digest(backup)==original
 (pkg/'uEnv.original.txt').write_bytes(env.read_bytes())
 result={'startup_files':before,'backup_sha256':digest(backup),'uEnv_sha256':digest(env),
         'free_FAT_bytes':free_bytes,'BOOT_name':boot.name,'BOOT_changed':False,'boot_id':old_boot_id}
 save('prepare.json',result)
finally:unmount()
print(json.dumps(result,indent=2))
''')
elif stage == 'transfer':
    assert json.loads((E / 'prepare/execution.json').read_text())['exit'] == 0
    out = E / 'transfer'
    out.mkdir(exist_ok=False)
    manifest = json.loads((C / 'controlled-startup-r5/manifest.json').read_text(encoding='utf-8'))
    for name in ['BOOT-hdmi-r5.bin', 'BOOT-original.bin', 'hdmi_static_probe']:
        source = C / 'controlled-startup-r5' / name
        assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest[name]['sha256']
        proc = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'put', str(source),
                               REMOTE + '/package/' + name, '--timeout', '30', '--log', str(out / (name + '.txt'))],
                              capture_output=True, timeout=40)
        dump(out / (name + '.execution.json'), {'exit': proc.returncode, 'budget': 30})
        assert proc.returncode == 0
    execute('verify-transfer', COMMON + r'''
assert digest(pkg/'BOOT-hdmi-r5.bin')==candidate
assert digest(pkg/'BOOT-original.bin')==digest(pkg/'BOOT-original.readback.bin')==original
assert digest(pkg/'hdmi_static_probe')=='590e689daf8f7b104f894145eb13232d59dea1f5491979457bcc1aa0ffd0c212'
os.chmod(pkg/'hdmi_static_probe',0o700)
print(json.dumps({'uploaded_bytes_verified':True,'BOOT_changed':False,'mounted':mounted(),'SDK_initialized':False}))
''')
    proc = subprocess.run([sys.executable, str(W / 'secure_transport.py'), 'get',
                           REMOTE + '/package/BOOT-original.readback.bin', str(out / 'BOOT-original.readback.bin'),
                           '--timeout', '30', '--log', str(out / 'backup-return.txt')], capture_output=True, timeout=40)
    assert proc.returncode == 0
    assert hashlib.sha256((out / 'BOOT-original.readback.bin').read_bytes()).hexdigest() == ORIGINAL
    dump(out / 'result.json', {'exit': 0, 'board_original_BOOT_returned_and_SHA_verified': True, 'BOOT_changed': False})
    print('Transfer verified; actual original BOOT read from board returned with exact SHA')
elif stage == 'install':
    assert json.loads((E / 'transfer/result.json').read_text())['exit'] == 0
    execute('install', COMMON + r'''
assert pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()==old_boot_id
assert digest(pkg/'BOOT-original.readback.bin')==digest(pkg/'BOOT-original.bin')==original
print(json.dumps(replace_boot(pkg/'BOOT-hdmi-r5.bin',original,candidate,'install.json'),indent=2))
''')
elif stage == 'restore':
    assert json.loads((E / 'install/execution.json').read_text())['exit'] == 0
    execute('restore-original-BOOT', COMMON + r'''
current=pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()
assert current!=old_boot_id,'Candidate startup not observed'
print(json.dumps(replace_boot(pkg/'BOOT-original.readback.bin',candidate,original,'restore.json'),indent=2))
''')
elif stage in ['read-only', 'bars', 'black']:
    assert json.loads((E / 'restore-original-BOOT/execution.json').read_text())['exit'] == 0
    # Preserve the binary's exact stdout/stderr/return status; SDK exceptions stop.
    code = COMMON + "\np=subprocess.run([str(pkg/'hdmi_static_probe'),'--" + stage + "'],capture_output=True,timeout=5)\n"
    code += "print(json.dumps({'exit':p.returncode,'stdout':p.stdout.decode(errors='replace'),'stderr':p.stderr.decode(errors='replace'),'mode':'" + stage + "','display_DMA_started':False},indent=2))\n"
    result = execute('probe-' + stage, code, budget=15)
    assert result['exit'] == 0, 'Probe failed; preserve and stop, no retry'
else:
    raise SystemExit('Expected prepare, transfer, install, restore, read-only, bars or black')
