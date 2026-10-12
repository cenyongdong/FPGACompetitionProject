"""Correct pre-transfer model-path/manifest assumptions; preserve unsent package."""
from pathlib import Path
import shutil,json,hashlib,tarfile
R=Path(__file__).resolve().parents[2];E=R/'tools/pose-v1/evidence/producer-contract-20261011-r2';B=R/'.local/pose-v1-build/producer-deployment-20261011-r2';out=E/'deployment-transfer-fixed';assert not out.exists();out.mkdir();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in (B/'pose_producer_deployment_log',B/'build-result.json',R/'tools/pose-v1/run-producer-deployment.sh',R/'tools/pose-v1/board_application_preflight.py'):shutil.copyfile(p,out/p.name)
(out/'files.sha256').write_text(''.join(sha(p)+'  '+p.name+'\n' for p in sorted(out.iterdir())),encoding='utf-8',newline='\n')
archive=E/'deployment-transfer-fixed.tar'
with tarfile.open(archive,'w') as t:
    for p in sorted(out.iterdir()):t.add(p,arcname=p.name)
(E/'deployment-transfer-fixed.identity.json').write_text(json.dumps({'archive_sha256':sha(archive),'program_sha256':sha(B/'pose_producer_deployment_log'),'runner_sha256':sha(R/'tools/pose-v1/run-producer-deployment.sh'),'reason':'Pre-transfer review corrected RAW graph path and exact frozen manifest hash. Original unsent archive preserved; no board retry.'},indent=2)+'\n',encoding='utf-8',newline='\n');print('Fixed transfer',sha(archive))
