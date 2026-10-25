from pathlib import Path
import subprocess,sys,shlex
W=Path(__file__).resolve().parent;BASE='/root/hdmi-render-speed-20261024-r47'
def call(name,mode,source,destination=None,timeout=60):
    argv=[sys.executable,str(W/'board_call.py'),name,mode,source]
    if destination:argv.append(destination)
    subprocess.run([*argv,'--timeout',str(timeout)],check=True)
code="from pathlib import Path;p=Path("+repr(BASE)+");p.mkdir(mode=0o700);print('New CPU-only renderer directory; no SDK/MMIO/BOOT')"
call('cpu-directory','ssh','python3 -c '+shlex.quote(code))
call('cpu-upload','put',str(W/'cpu-benchmark.tar.gz'),BASE+'/cpu-benchmark.tar.gz')
code='''from pathlib import Path
import json,hashlib,tarfile,subprocess,os,time
p=Path(BASE)
boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
if boot!='85ec60a1-99d6-4fe8-9290-6abe5d935b1d':raise RuntimeError('Expected original runtime changed')
owners=[]
for f in Path('/proc').glob('[0-9]*/fd/*'):
 try:
  target=os.readlink(str(f))
  if target.startswith(('/dev/axi','/dev/udmabuf','/dev/u-dma','/dev/video')):owners.append([str(f),target])
 except OSError:pass
if owners:raise RuntimeError('Concurrent device owner; defer CPU benchmark')
with tarfile.open(p/'cpu-benchmark.tar.gz') as t:
 for m in t.getmembers():
  if not m.isfile() or '..' in Path(m.name).parts or Path(m.name).is_absolute():raise RuntimeError('Unexpected file')
 t.extractall(p)
manifest=json.loads((p/'cpu-manifest.json').read_text())
if not all(hashlib.sha256((p/n).read_bytes()).hexdigest()==s for n,s in manifest.items()):raise RuntimeError('CPU package differs')
exe=p/'renderer_bench';exe.chmod(0o700);out=p/'cpu-output';out.mkdir(mode=0o700)
with (p/'cpuinfo.txt').open('wb') as f:f.write(Path('/proc/cpuinfo').read_bytes())
with (p/'meminfo-before.txt').open('wb') as f:f.write(Path('/proc/meminfo').read_bytes())
with (p/'stdout.json').open('xb') as so,(p/'stderr.log').open('xb') as se:
 start=time.monotonic();r=subprocess.run([str(exe),str(p/'fixtures'),str(out),'10'],stdout=so,stderr=se,timeout=30)
record=dict(native_exit=r.returncode,seconds=time.monotonic()-start,SDK=0,MMIO=0,BOOT_writes=0,reboots=0,
            boot_id_before=boot,boot_id_after=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),automatic_retry=False)
with (p/'cpu-execution.json').open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(record));print((p/'stdout.json').read_text());print((p/'stderr.log').read_text())
if r.returncode:raise SystemExit(r.returncode)
'''.replace('BASE',repr(BASE))
call('cpu-execute','ssh','python3 -c '+shlex.quote(code),timeout=60)
