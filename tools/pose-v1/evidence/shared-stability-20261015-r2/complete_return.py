"""Monitor the existing evidence archiver, then return it; never starts inference."""
from pathlib import Path
import hashlib,json,shlex,subprocess,sys,tarfile,time,shutil
E=Path(__file__).resolve().parent
R=E.parents[3]
T=R/'.local/shared-stability-transport-20261015-r2/secure_transport.py'
B='/tmp/wifi-pose-shared-stability-20261015-r2'
def call(mode,source,destination,log,timeout=30):
    args=[sys.executable,str(T),mode,source]
    if destination:args.append(str(destination))
    args+=['--timeout',str(timeout),'--log',str(E/(log+'.txt'))]
    p=subprocess.run(args,capture_output=True)
    if p.returncode:
        (E/(log+'-transport-error.txt')).write_bytes(p.stdout+p.stderr)
        raise RuntimeError('Evidence transport stopped: '+log)
    return p.stdout
started=time.monotonic()
for i in range(32):
    code="""from pathlib import Path
import json
p=Path('/proc/95662');r=Path(B);a=r/'stress.tar.xz'
running=False
if p.exists():
 s=(p/'stat').read_text().rsplit(')',1)[1].split()
 if s[0]!='Z':
  assert s[19]=='2292949', 'Archiver identity changed'
  assert b'tarfile' in (p/'cmdline').read_bytes()
  running=True
with a.open('rb') as f:
 f.seek(-2,2);footer=f.read().hex()
print(json.dumps(dict(archiver_running=running,archive_bytes=a.stat().st_size,xz_footer_hex=footer)))
""".replace('Path(B)','Path('+repr(B)+')')
    state=json.loads(call('ssh','python3 -c '+shlex.quote(code),None,'archive-watch-'+str(i)))
    print(json.dumps(state),flush=True)
    if not state['archiver_running']:
        assert state['xz_footer_hex']=='595a','Incomplete xz footer; preserve artifact'
        break
    if i==31:raise RuntimeError('Evidence archiver observation budget ended; no inference retry')
    time.sleep(43)
dest=E/'stress.tar.xz';assert not dest.exists()
call('get',B+'/stress.tar.xz',dest,'return-stress-completed',180)
out=E/'returned-stress';assert not out.exists();out.mkdir()
with tarfile.open(dest) as t:
    for m in t:
        p=(out/m.name).resolve();assert out.resolve() in p.parents
        assert m.isfile() or m.isdir()
        if m.isdir():p.mkdir(parents=True,exist_ok=True)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as f,p.open('xb') as w:shutil.copyfileobj(f,w)
record=dict(status='complete_return',inference_restarted=False,prior_operation='archive SSH timed out at 180 seconds; existing archiver retained',
    archive_bytes=dest.stat().st_size,archive_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),return_observation_seconds=time.monotonic()-started)
(E/'archive-return-recovery.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record),flush=True)
