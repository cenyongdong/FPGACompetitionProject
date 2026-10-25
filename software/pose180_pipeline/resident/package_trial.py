"""Prepare the concrete 90-second original-BOOT resident trial, without devices."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.local/pose180-resident-20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    package=OUT/'package';package.mkdir()
    shutil.copyfile(OUT/'arm64/pose180_demo',package/'pose180_demo')
    shutil.copyfile(Path(__file__).with_name('run_board.py'),package/'run_board.py')
    shutil.copyfile(ROOT/'demo_v1/tools/preflight.py',package/'preflight.py')
    original=json.loads((ROOT/'.local/pose180-deploy-20261024-r3/package/identity.json').read_text())
    model_package='/root/demo-v1-20261022-r1/pose180-pipeline-20261025-r1'
    model_files={key:value for key,value in original['files'].items() if key.startswith('models/')}
    identity=dict(session=202610250501,model_package=model_package,model_files=model_files,
        libraries=original['libraries'],boot_files=original['expected_boot_files'],
        boot_id='2d5f618a-7891-493e-a519-714c0edcaa3c',
        files={p.name:sha(p) for p in package.iterdir() if p.is_file()},
        SDK_attempts=1,seconds=90,hdmi=False,CSI_live=False,BOOT_writes=0,reboots=0,automatic_retry=False)
    (package/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    with tarfile.open(OUT/'package.tar.gz','x:gz') as archive:
        for p in package.iterdir():
            info=archive.gettarinfo(str(p),p.name);info.mode=0o755 if p.name=='pose180_demo' else 0o644
            with p.open('rb') as source:archive.addfile(info,source)
    print(json.dumps({'archive':str(OUT/'package.tar.gz'),'identity':identity['files']}))
if __name__=='__main__':main()
