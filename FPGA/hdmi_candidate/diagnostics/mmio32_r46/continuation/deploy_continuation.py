from pathlib import Path
import json,subprocess,sys,shlex
W=Path(__file__).resolve().parent;D=W/'continuation'
BASE='/root/hp2-mmio32-20261024-r46'
expected=json.loads((D/'archive-identity.json').read_text())['sha256']
code='''from pathlib import Path
import json,hashlib,tarfile,shutil,os
p=Path(BASE)
digest=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
need=lambda ok,why:None if ok else (_ for _ in ()).throw(RuntimeError(why))
need(Path('/proc/sys/kernel/random/boot_id').read_text().strip()=='ca5ae553-4b37-4daf-b30c-84746f081176','Same-boot continuation lost')
a=p/'continuation-r46.tar.gz';need(digest(a)==EXPECTED,'Archive transfer differs')
old=json.loads((p/'config.json').read_text());backup=p/'pre-continuation-code';backup.mkdir(mode=0o700)
stop=p/'metadata/stopped.json';failed=p/'run-1/consume/capture/result.json';raw=p/'run-1/consume/capture/raw.jsonl'
preserved={str(f.relative_to(p)):digest(f) for f in (stop,failed,raw)}
with tarfile.open(a) as t:
 members=t.getmembers()
 need(all(m.isfile() and '..' not in Path(m.name).parts and not Path(m.name).is_absolute() for m in members),'Invalid member')
 for m in members:
  f=p/m.name
  if f.exists():
   if m.name=='ps_release_board.py':need(digest(f)==old['controller_files'][m.name]['sha256'],'Original parent changed')
   elif m.name.startswith('package/'):need(digest(f)==old['files'][f.name]['sha256'],'Original collector changed')
   target=backup/m.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
 # No load is running. All command files are replaced together before entry.
 t.extractall(p)
for f in [p/'ps_release_board.py',*(p/'package').glob('*.py')]:compile(f.read_text(),str(f),'exec')
need(all(digest(p/name)==value for name,value in preserved.items()),'Original failed evidence changed')
record=dict(installed=True,same_boot=True,BOOT_write=False,MMIO=0,SDK=0,original_failed_evidence=preserved,archive_sha256=EXPECTED)
with (p/'metadata/continuation-installed.json').open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(record))
'''.replace('BASE',repr(BASE)).replace('EXPECTED',repr(expected))
subprocess.run([sys.executable,str(W/'board_call.py'),'continuation-install','ssh','python3 -c '+shlex.quote(code),'--timeout','60'],check=True)
