"""Deploy one finite, identity-checked package; always preserve its complete return."""
import json
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

R=Path(r'D:\FPGACompetitionProject')
E=R/'tools/pose-v1/evidence/noscatter-board-20261015-r1'
T=R/'.local/noscatter-transport-20261015-r1/secure_transport.py'
P=json.loads((E/'execution-plan.json').read_text(encoding='utf-8'))
remote=P['remote']
steps=json.loads((E/'steps.json').read_text(encoding='utf-8')) if (E/'steps.json').exists() else []
def call(mode,source,destination,stem,timeout):
    cmd=[sys.executable,str(T),mode,source]
    if destination:cmd.append(destination)
    cmd+=['--timeout',str(timeout),'--log',str(E/(stem+'.txt'))]
    proc=subprocess.run(cmd,capture_output=True)
    sys.stdout.buffer.write(proc.stdout+proc.stderr);sys.stdout.flush()
    steps.append(dict(stage=stem,exit=proc.returncode,argv=cmd))
    (E/'steps.json').write_bytes((json.dumps(steps,indent=2)+'\n').encode())
    return proc.returncode
def code(s):return 'python3 -c '+shlex.quote(s)
if not any(s['stage']=='03-transfer' and s['exit']==0 for s in steps):
    assert call('put',str(E/'transfer.tar'),remote+'/transfer.tar','03-transfer',120)==0
install="""from pathlib import Path
import hashlib,tarfile
r=Path(REMOTE);p=r/'transfer.tar'
assert hashlib.sha256(p.read_bytes()).hexdigest()==SHA
with tarfile.open(p) as t:
 assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in t)
 t.extractall(r)
b=r/'pose_noscatter_timing';b.chmod(b.stat().st_mode|0o100)
""".replace('REMOTE',repr(remote)).replace('SHA',repr(P['transfer_sha256']))
compile(install,'remote-install','exec')
assert call('ssh',code(install),None,'04-install-r2',30)==0
exit_code=call('ssh','cd '+shlex.quote(remote)+' && python3 board_run.py --mode wall --cycles 1',None,'05-execute',160)
archive="""from pathlib import Path
import tarfile
r=Path(REMOTE);a=r/'return.tar';assert not a.exists()
with tarfile.open(a,'x') as t:
 for name in ('run-wall','package.json'):
  t.add(r/name,arcname=name)
""".replace('REMOTE',repr(remote))
assert call('ssh',code(archive),None,'06-archive',30)==0
assert call('get',remote+'/return.tar',str(E/'return.tar'),'07-return',90)==0
dest=E/'returned';assert not dest.exists();dest.mkdir()
with tarfile.open(E/'return.tar') as t:
    for m in t:
        path=(dest/m.name).resolve()
        assert dest.resolve() in path.parents or path==dest.resolve()
        assert m.isfile() or m.isdir()
        if m.isdir():path.mkdir(parents=True,exist_ok=True)
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            with t.extractfile(m) as f,path.open('xb') as w:
                import shutil
                shutil.copyfileobj(f,w)
result=dict(status='board_run_returned',execute_exit=exit_code,
            output=str(dest),retry=False,reference_gate_relaxed=False)
(E/'return-status.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
print(json.dumps(result),flush=True)
sys.exit(exit_code)
