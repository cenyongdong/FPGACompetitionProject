from pathlib import Path
import shutil,json,tarfile,hashlib
W=Path(__file__).resolve().parent;O=Path('D:/FPGACompetitionProject')
old=O/'.local/hp2-mmio32-20261024-r46'
for name in ('native_transport.py','board_call.py'):
    source=(old/name).read_text().replace('hp2-mmio32-20261024-r46','hdmi-render-speed-20261024-r47')
    (W/name).write_bytes(source.encode())
shutil.copyfile(old/'NativeAskpass.exe',W/'NativeAskpass.exe')
manifest={p.relative_to(W).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
          for p in [W/'renderer_bench',*sorted((W/'fixtures').glob('*.f32'))]}
(W/'cpu-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
with tarfile.open(W/'cpu-benchmark.tar.gz','x:gz') as t:
    for name in [*manifest,'cpu-manifest.json']:t.add(W/name,arcname=name)
print('Prepared CPU-only board benchmark; SDK/MMIO/BOOT=0.')
