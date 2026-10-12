"""Bind the compiled probe and independent runner into a fresh transfer archive."""
from pathlib import Path
import hashlib,json,shutil,tarfile
R=Path(__file__).resolve().parents[2];B=R/'.local/pose-v1-build/axi-pair-20261011-r4';P=R/'.local/pose-v1-axi-pair/package-20261011-r4';E=R/'tools/pose-v1/evidence/axi-pair-20261011-r4'
assert not E.exists();E.mkdir()
bundle=E/'transfer';bundle.mkdir();shutil.copytree(P,bundle/'package')
for name in ('pose_axi_pair_check','pose_axi_pair_host_check','build-result.json'):shutil.copyfile(B/name,bundle/name)
for name in ('board_application_preflight.py','run-axi-pair.sh'):shutil.copyfile(R/'tools/pose-v1'/name,bundle/name)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(bundle/'files.sha256').write_text(''.join(sha(p)+'  '+p.relative_to(bundle).as_posix()+'\n' for p in sorted(bundle.rglob('*')) if p.is_file()),encoding='utf-8',newline='\n')
archive=E/'transfer.tar'
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as t:
    for p in sorted(bundle.rglob('*')):
        if p.is_file():t.add(p,arcname=p.relative_to(bundle).as_posix())
(E/'transfer.identity.json').write_text(json.dumps({'sha256':sha(archive),'files':sum(p.is_file() for p in bundle.rglob('*')),'manifest_sha256':sha(P/'manifest.json'),'program_sha256':sha(B/'pose_axi_pair_check')},indent=2)+'\n',encoding='utf-8',newline='\n')
print('Transfer archive',sha(archive))
