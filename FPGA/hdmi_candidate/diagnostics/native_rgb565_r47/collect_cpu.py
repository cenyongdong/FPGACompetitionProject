from pathlib import Path
import sys,subprocess,shlex,json,hashlib,tarfile
W=Path(__file__).resolve().parent;E=Path('D:/FPGACompetitionProject/tools/pose-v1/evidence/hdmi-render-speed-20261024-r47')
BASE='/root/hdmi-render-speed-20261024-r47'
def call(name,mode,source,destination=None):
    a=[sys.executable,str(W/'board_call.py'),name,mode,source]
    if destination:a.append(str(destination))
    subprocess.run(a,check=True)
code='''from pathlib import Path
import tarfile,json,hashlib
p=Path(BASE);a=p/'cpu-evidence.tar.gz'
with tarfile.open(a,'x:gz') as t:
 for f in [p/'cpu-execution.json',p/'stdout.json',p/'stderr.log',p/'cpuinfo.txt',p/'meminfo-before.txt',p/'cpu-manifest.json',*sorted((p/'cpu-output').glob('*.rgb565'))]:t.add(f,arcname=f.relative_to(p).as_posix())
print(json.dumps(dict(bytes=a.stat().st_size,sha256=hashlib.sha256(a.read_bytes()).hexdigest())))
'''.replace('BASE',repr(BASE))
call('cpu-archive','ssh','python3 -c '+shlex.quote(code))
expected=json.loads((E/'cpu-archive.log').read_text().strip())
archive=E/'cpu-evidence.tar.gz';call('cpu-download','get',BASE+'/cpu-evidence.tar.gz',archive)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected['sha256']
out=W/'board-cpu';out.mkdir()
with tarfile.open(archive) as t:
    assert all(m.isfile() and out.resolve() in (out/m.name).resolve().parents for m in t.getmembers())
    t.extractall(out)
result=json.loads((out/'stdout.json').read_text());execution=json.loads((out/'cpu-execution.json').read_text())
assert execution['native_exit']==0 and execution['boot_id_before']==execution['boot_id_after'] and result['model_values_preserved'] and result['skeleton_scale_preserved']
result['draw_plus_convert_speedup']=(result['old_draw']['mean_ms']+result['old_canvas']['mean_ms'])/result['native_RGB565']['mean_ms']
for name,value in [('board-cpu.json',result),('cpu-execution.json',execution),('archive-identity.json',expected)]:
    (E/name).write_bytes((json.dumps(value,indent=2)+'\n').encode())
print(json.dumps(result))
