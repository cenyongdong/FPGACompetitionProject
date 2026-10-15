"""Freeze exact new model, ARM executable and the three old comparison fixtures."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

R=Path(r'D:\FPGACompetitionProject')
E=R/'tools/pose-v1/evidence/noscatter-board-20261015-r1'
D=R/'.local/noscatter-delivery-20261015-r1'
S=R/'.local/noscatter-source-20261015-r1'
OLD=R/'.local/engine-timing-delivery-20261013-r3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((OLD/'package.json').read_text(encoding='utf-8'))
assert (D/'pose_noscatter_timing').read_bytes()[:6]==b'\x7fELF\x02\x01'
assert int.from_bytes((D/'pose_noscatter_timing').read_bytes()[18:20],'little')==183
for f in ('board_run.py','board_application_preflight.py'):ast.parse((D/f).read_text(encoding='utf-8'))
for f in (D/'fixtures').iterdir():assert f.read_bytes()==(OLD/'fixtures'/f.name).read_bytes()
run=subprocess.run(['docker','exec','FPAI','sha256sum',*['/usr/lib/aarch64-linux-gnu/'+n for n in p['libraries']]],capture_output=True,check=True)
(E/'docker-sdk-sha256.txt').write_bytes(run.stdout+run.stderr)
actual={Path(line.split()[1]).name:line.split()[0] for line in run.stdout.decode().splitlines()}
assert actual==p['libraries']
p.update(status='new_model_delivery_prepared_not_board_executed',
    binary_sha256=sha(D/'pose_noscatter_timing'),source_manifest_sha256=sha(D/'source-manifest.json'),
    model_changed=True,ScatterND_count=0,host_compute_ids=[188,192,437,442],
    source_directory=str(S),expected_frames=3,child_budget_seconds=120,
    old_DATA_investigation_resumed=False,SDK_hardware_profile_disabled=True,
    strict_comparison='All100 scores and all4200 coordinates bitwise vs saved original board outputs; stop on mismatch')
p['files']={str(f.relative_to(D)).replace('\\','/'):sha(f) for f in sorted(D.rglob('*')) if f.is_file()}
(D/'package.json').write_bytes((json.dumps(p,indent=2)+'\n').encode())
shutil.copyfile(D/'package.json',E/'package.json')
archive=E/'transfer.tar'
with tarfile.open(archive,'x') as tar:
    for f in sorted(D.rglob('*')):
        if f.is_file():tar.add(f,arcname=str(f.relative_to(D)).replace('\\','/'))
with tarfile.open(archive,'r') as tar:assert all(m.isfile() and not Path(m.name).is_absolute() and '..' not in Path(m.name).parts for m in tar)
plan=dict(remote='/tmp/wifi-pose-noscatter-20261015-r1',transfer_sha256=sha(archive),
    package_sha256=sha(D/'package.json'),transfer_bytes=archive.stat().st_size,
    frames=3,mode='wall',child_budget_seconds=120,kill_grace_seconds=5,
    reference='Same S11_01_308/309/310 original board inputs/scores/poses as 2026-10-13 timing',
    stop='Any error, identity drift, nonfinite, illegal index, output byte discrepancy, timeout, kernel log change',
    VPU_TCP=False,reboot=False,automatic_retry=False)
(E/'execution-plan.json').write_bytes((json.dumps(plan,indent=2)+'\n').encode())
print(json.dumps(plan))
