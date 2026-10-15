"""Retrieve the complete remote export and verify its archive and member identities."""
import hashlib,json
from pathlib import Path
import shutil,subprocess,tarfile
R=Path(r'D:\FPGACompetitionProject');E=Path(__file__).resolve().parent
ALG=Path(r'D:\Person-in-WIFI-3D\Person-in-WiFi-3D-repo')
prefix='gpu-server:/public/cyd/Person-in-WiFi-3D-repo/exportONNX/shared-refine-20261015-r1'
for suffix,dest in [('.archive.json',E/'export-archive.json'),('.tar.gz',E/'export.tar.gz')]:
    assert not dest.exists()
    subprocess.run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes',prefix+suffix,str(dest)],check=True,timeout=120)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((E/'export-archive.json').read_text())
assert sha(E/'export.tar.gz')==meta['sha256'] and (E/'export.tar.gz').stat().st_size==meta['bytes']
out=(ALG/'exportONNX/shared-refine-20261015-r1').resolve()
with tarfile.open(E/'export.tar.gz') as tar:
    for member in tar:
        path=(out.parent/member.name).resolve()
        assert path==out or out in path.parents
        assert member.isdir() or member.isfile()
        if member.isdir():path.mkdir(exist_ok=True,parents=True)
        else:
            path.parent.mkdir(exist_ok=True,parents=True)
            with tar.extractfile(member) as f:
                if path.exists():assert path.read_bytes()==f.read(),str(path)
                else:
                    with path.open('xb') as d:shutil.copyfileobj(f,d)
assert (out/'exit-code.txt').read_text().strip()=='0' and not (out/'failure.json').exists()
for name,h in json.loads((out/'files.json').read_text()).items():assert sha(out/name)==h,name
summary=json.loads((out/'summary.json').read_text());assert sha(out/summary['file'])==summary['sha256']
for name in ('summary.json','preflight.json','verification.json','refine-matmul-shapes.json','execution.json'):
    shutil.copyfile(out/name,E/('export-'+name))
review=dict(status='complete_export_return_and_member_hashes_verified',path=str(out),onnx_sha256=summary['sha256'],
              archive_sha256=meta['sha256'],samples=summary['samples'],TopK=2,ScatterND=0)
(E/'onnx-local-review.json').write_bytes((json.dumps(review,indent=2)+'\n').encode())
print(json.dumps(review))
