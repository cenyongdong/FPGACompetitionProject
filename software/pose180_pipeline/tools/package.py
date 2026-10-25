"""Prepare one deployable software package without contacting any device."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.local/pose180-pipeline-20261025-r1'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    package=OUT/'package';package.mkdir()
    shutil.copyfile(OUT/'arm64/pose180_pipeline',package/'pose180_pipeline')
    shutil.copyfile(Path(__file__).with_name('run_board.py'),package/'run_board.py')
    shutil.copyfile(ROOT/'demo_v1/tools/preflight.py',package/'preflight.py')
    model=ROOT/'model/piw24_pose180_shared-20261024-r1'
    (package/'models').mkdir()
    for name in ('piw24_pose180_ZG.json','piw24_pose180_ZG.raw'):
        shutil.copyfile(model/name,package/'models'/name)
    original=json.loads((ROOT/'.local/pose180-deploy-20261024-r3/package/identity.json').read_text())
    for name in ('piw24_pose180_ZG.json','piw24_pose180_ZG.raw'):
        if sha(package/'models'/name)!=original['files']['models/'+name]:
            raise ValueError('Model differs from the already deployed epoch99 candidate: '+name)
    identity=dict(model='piw24_pose180_shared epoch99',candidate_count=180,Host_compute=0,
        full_schema='PIWFUL3/3',full_bytes=74544,CSI_live=False,SDK_libraries=original['libraries'],
        protected_original_boot_files=original['expected_boot_files'],
        files={p.relative_to(package).as_posix():sha(p) for p in sorted(package.rglob('*')) if p.is_file()},
        numerical_accuracy_accepted=False,stability_policy='Complete first outputs, finite/identity/selection/completion checks; D48 numerical errors remain open',
        planned_frames=52800,planned_hz=30,planned_hard_seconds=2100,
        execution_state='software_ready_board_deferred_by_user',BOOT_authorization_added=False,automatic_retry=False)
    (package/'identity.json').write_text(json.dumps(identity,indent=2)+'\n')
    archive=OUT/'software-package.tar.gz'
    with tarfile.open(archive,'x:gz') as stream:
        for path in sorted(package.rglob('*')):
            if path.is_file():
                info=stream.gettarinfo(str(path),arcname=path.relative_to(package).as_posix())
                info.mode=0o755 if path.name=='pose180_pipeline' else 0o644
                with path.open('rb') as source:stream.addfile(info,source)
    state=dict(status='software_ready_board_deferred_by_user',SDK_Open=0,BOOT_writes=0,reboots=0,CSI_live=False,
        actual_board_stability_verified=False,archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
        board_network_observation='PC Ethernet disconnected; initial read-only SSH timed out; user says board unavailable',
        original_failed_build_preserved=True)
    (OUT/'state.json').write_text(json.dumps(state,indent=2)+'\n');print(json.dumps(state))


if __name__=='__main__':main()
