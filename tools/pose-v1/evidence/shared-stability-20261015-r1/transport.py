"""Fresh, finite transport actions; uses pinned OpenSSH credentials in memory only."""
from pathlib import Path
import json,shlex,subprocess,sys,tarfile
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
T=R/'.local/shared-stability-transport-20261015-r1/secure_transport.py'
P=json.loads((E/'transfer.json').read_text(encoding='utf-8'));remote=P['remote']
def call(mode,source,destination,log,timeout):
    cmd=[sys.executable,str(T),mode,source]
    if destination:cmd.append(destination)
    cmd+=['--timeout',str(timeout),'--log',str(E/(log+'.txt'))]
    p=subprocess.run(cmd,capture_output=True);sys.stdout.buffer.write(p.stdout+p.stderr);sys.stdout.flush()
    if p.returncode:raise RuntimeError('Transport stopped: '+log+' exit '+str(p.returncode))
def command(s):return 'python3 -c '+shlex.quote(s)
action=sys.argv[1]
if action=='deploy':
    call('ssh','mkdir -- '+remote,None,'03-create',20)
    call('put',str(E/'transfer.tar'),remote+'/transfer.tar','04-transfer',120)
    code="""from pathlib import Path
import hashlib,tarfile
r=Path(REMOTE);p=r/'transfer.tar';assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
with tarfile.open(p) as t:
 assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in t)
 t.extractall(r)
for n in ('pose_shared_timing','pose_shared_resident'):
 b=r/n;b.chmod(b.stat().st_mode|0o100)
""".replace('REMOTE',repr(remote)).replace('SHA',repr(P['transfer_sha256']))
    call('ssh',command(code),None,'05-install',30)
elif action=='basic':
    call('ssh','cd '+shlex.quote(remote)+' && python3 run_stage.py --stage basic',None,'06-basic',180)
elif action=='short':
    call('ssh','cd '+shlex.quote(remote)+' && python3 run_stage.py --stage short',None,'09-short',180)
elif action.startswith('return-'):
    stage=action[7:];assert stage in ('basic','short','stress')
    code="""from pathlib import Path
import tarfile
r=Path(REMOTE);p=r/(STAGE+'.tar.xz');assert not p.exists()
with tarfile.open(p,'x:xz',preset=1) as t:
 t.add(r/('run-'+STAGE),arcname='run-'+STAGE)
""".replace('REMOTE',repr(remote)).replace('STAGE',repr(stage))
    call('ssh',command(code),None,'archive-'+stage,180)
    dest=E/(stage+'.tar.xz');call('get',remote+'/'+dest.name,str(dest),'return-'+stage,180)
    out=E/('returned-'+stage);assert not out.exists();out.mkdir()
    with tarfile.open(dest) as t:
        for m in t:
            path=(out/m.name).resolve();assert out.resolve() in path.parents or path==out.resolve()
            assert m.isfile() or m.isdir()
            if m.isdir():path.mkdir(parents=True,exist_ok=True)
            else:
                path.parent.mkdir(parents=True,exist_ok=True)
                with t.extractfile(m) as f,path.open('xb') as w:
                    import shutil
                    shutil.copyfileobj(f,w)
    print('Complete returned',stage,flush=True)
else:raise RuntimeError('Unsupported finite transport action')
