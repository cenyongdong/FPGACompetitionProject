from pathlib import Path
import subprocess,sys,json,shlex
W=Path(__file__).resolve().parent;E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-long-native-20261024-r48');BASE='/root/hdmi-long-native-20261024-r48'
def call(name,mode,source,destination=None,timeout=120):
    a=[sys.executable,str(W/'board_call.py'),name,mode,source]
    if destination:a.append(str(destination))
    subprocess.run([*a,'--timeout',str(timeout)],check=True)
code="from pathlib import Path;p=Path("+repr(BASE)+");p.mkdir(mode=0o700);(p/'metadata').mkdir(mode=0o700);(p/'package').mkdir(mode=0o700);(p/'boot-mount').mkdir(mode=0o700);print('New single-start long package directory created')"
call('deploy-directory','ssh','python3 -c '+shlex.quote(code))
call('deploy-upload','put',W/'deploy-r48-board.tar.gz',BASE+'/deploy-r48-board.tar.gz')
expected=json.loads((E/'deployment-identity.json').read_text())['sha256']
code='''from pathlib import Path
import hashlib,tarfile,json,shutil
p=Path(BASE);digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
if digest(p/'deploy-r48-board.tar.gz')!=EXPECTED:raise RuntimeError('Deployment transfer differs')
with tarfile.open(p/'deploy-r48-board.tar.gz') as t:
 for m in t.getmembers():
  if not m.isfile() or '..' in Path(m.name).parts or Path(m.name).is_absolute():raise RuntimeError('Invalid deployment file')
 t.extractall(p)
cfg=json.loads((p/'config.json').read_text())
for name,source in cfg['asset_reuse'].items():
 f=Path(source);row=cfg['files'][name]
 if f.stat().st_size!=row['bytes'] or digest(f)!=row['sha256']:raise RuntimeError('Prior file asset changed: '+name)
 target=p/'package'/name
 if target.exists():raise RuntimeError('Unexpected existing reused asset')
 shutil.copyfile(f,target)
with tarfile.open(p/'package/software.tar.gz') as t:
 for m in t.getmembers():
  if not (m.isfile() or m.isdir()) or '..' in Path(m.name).parts or Path(m.name).is_absolute() or not m.name.startswith('software/'):raise RuntimeError('Invalid software payload')
 t.extractall(p)
for f in [p/'ps_release_board.py',p/'bootstrap.py',*(p/'package').glob('*.py'),p/'software/board_guard.py']:
 compile(f.read_text(),str(f),'exec')
print(json.dumps(dict(prepared=True,BOOT_writes=0,SDK=0,python_files_checked=True,reused_files=list(cfg['asset_reuse']))))
'''.replace('BASE',repr(BASE)).replace('EXPECTED',repr(expected))
call('deploy-extract','ssh','python3 -c '+shlex.quote(code))
call('prepare-identity','ssh','python3 '+BASE+'/ps_release_board.py prepare')
state=json.loads((E/'state.json').read_text());state.update(status='deployed_prepared_no_BOOT_write',uploaded=True)
(E/'state.json').write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode())
