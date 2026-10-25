from pathlib import Path
import json, shlex, shutil, subprocess, sys
w=Path(__file__).resolve().parent;e=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-overlap-20261024-r51')
old=w.with_name('hdmi-ack-transport-20261024-r50')
for name in ('board_call.py','native_transport.py'):
    (w/name).write_text((old/name).read_text().replace('hdmi-ack-transport-20261024-r50','hdmi-render-overlap-20261024-r51'))
shutil.copyfile(old/'NativeAskpass.exe',w/'NativeAskpass.exe')
base='/root/hdmi-render-overlap-20261024-r51'
def call(name,mode,source,destination=None):
    argv=[sys.executable,str(w/'board_call.py'),name,mode,source]
    if destination:argv.append(destination)
    subprocess.run([*argv,'--timeout','60'],check=True)
if not (e/'put-CPU-package.log').exists():
    call('prepare-CPU-only','ssh','mkdir '+base+' && cat /proc/sys/kernel/random/boot_id')
    call('put-CPU-package','put',str(w/'cpu-package.tar.gz'),base+'/cpu-package.tar.gz')
digest=json.loads((e/'build-result.json').read_text())['cpu_archive_sha256']
code=r'''from pathlib import Path
import hashlib,json,os,subprocess,tarfile,time
p=Path(BASE);boot=lambda:Path('/proc/sys/kernel/random/boot_id').read_text().strip()
before=boot()
if before!='ef19aa67-8848-40c6-b4a2-df9da7e4be68':raise RuntimeError('Original runtime changed')
if hashlib.sha256((p/'cpu-package.tar.gz').read_bytes()).hexdigest()!=DIGEST:raise RuntimeError('CPU transfer differs')
with tarfile.open(p/'cpu-package.tar.gz') as t:
 if not all((m.isfile() or m.isdir()) and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in t.getmembers()):raise RuntimeError('Unsafe CPU member')
 t.extractall(p)
os.chmod(p/'renderer_overlap_bench',0o700)
start=time.monotonic()
with (p/'cpu.stdout.log').open('xb') as so,(p/'cpu.stderr.log').open('xb') as se:
 result=subprocess.run([str(p/'renderer_overlap_bench'),str(p/'fixtures'),str(p/'golden')],stdin=subprocess.DEVNULL,stdout=so,stderr=se)
record=dict(native_exit=result.returncode,seconds=time.monotonic()-start,boot_id=boot(),boot_unchanged=before==boot(),SDK=0,MMIO=0,BOOT_writes=0,reboots=0)
(p/'cpu-execution.json').write_text(json.dumps(record,indent=2)+'\n')
print((p/'cpu.stdout.log').read_text(),end='');print((p/'cpu.stderr.log').read_text(),end='');print(json.dumps(record),flush=True)
raise SystemExit(result.returncode or (0 if before==boot() else 2))
'''.replace('BASE',repr(base)).replace('DIGEST',repr(digest))
call('board-CPU-regression','ssh','python3 -c '+shlex.quote(code))
call('get-CPU-record','get',base+'/cpu-execution.json',str(e/'cpu-execution.json'))
call('get-CPU-stdout','get',base+'/cpu.stdout.log',str(e/'cpu.stdout.log'))
call('get-CPU-stderr','get',base+'/cpu.stderr.log',str(e/'cpu.stderr.log'))
