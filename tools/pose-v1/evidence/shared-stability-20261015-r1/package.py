from pathlib import Path
import ast,hashlib,json,shutil,tarfile
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
D=R/'.local/shared-stability-delivery-20261015-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
original=R/'.local/shared-confidence-delivery-20261015-r1'
p=json.loads((original/'package.json').read_text(encoding='utf-8'))
assert sha(D/'pose_shared_timing')==p['binary_sha256']=='4c01c92cca92e5d76f427e121fa5c770f61dff3de49a26a75bf3d3fe20351070'
for name in ('pose_shared_timing','pose_shared_resident'):
    b=(D/name).read_bytes();assert b[:6]==b'\x7fELF\x02\x01' and int.from_bytes(b[18:20],'little')==183
for name in ('models','fixtures'):
    for f in (D/name).iterdir():assert sha(f)==sha(original/name/f.name)
for f in D.glob('*.py'):ast.parse(f.read_text(encoding='utf-8'))
p.update(status='stability_test_package_prepared_not_executed',resident_binary_sha256=sha(D/'pose_shared_resident'),
    resident_source_manifest_sha256=sha(D/'resident-source-manifest.json'),
    original_validation_binary_unchanged=True,phase_plan=json.loads((D/'plan.json').read_text(encoding='utf-8')))
p['files']={f.relative_to(D).as_posix():sha(f) for f in sorted(D.rglob('*')) if f.is_file()}
save(D/'package.json',p);shutil.copyfile(D/'package.json',E/'package.json')
archive=E/'transfer.tar'
with tarfile.open(archive,'x') as t:
    for f in sorted(D.rglob('*')):
        if f.is_file():t.add(f,arcname=f.relative_to(D).as_posix(),recursive=False)
save(E/'transfer.json',dict(remote='/tmp/wifi-pose-shared-stability-20261015-r1',
    transfer_sha256=sha(archive),transfer_bytes=archive.stat().st_size,package_sha256=sha(D/'package.json')))
print('Package frozen',archive.stat().st_size)
