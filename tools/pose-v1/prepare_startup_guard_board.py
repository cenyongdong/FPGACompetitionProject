"""Prepare three fresh independent-start folders from the frozen board baseline."""
import hashlib,json,shutil
from pathlib import Path
source=Path('/tmp/pose-stage-guard-20261009-r1')
root=Path('/tmp/pose-startup-guard-20261009-r1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not root.exists()
assert sha(source/'pose_live_pipeline_check')=='27b9ff09278daa2232f320af37183a7d41a7e7d74cdbbee5a30d747d2769e086'
assert sha(source/'package/manifest.json')=='de32738d0322923b59295a206f42b3ac6e42d6a2b7a7107820a5e78aa96ed48d'
for gate in ('build','host-check','process-three'):
    g=json.loads((source/'gates'/f'{gate}.acceptance.json').read_text())
    assert g['binary_sha256']==sha(source/'pose_live_pipeline_check') and g['package_manifest_sha256']==sha(source/'package/manifest.json')
root.mkdir()
names=['pose_live_pipeline_check','pose_display_worker','build-result.json','run-stage-guard.sh','board_application_preflight.py']
for i in range(1,4):
    out=root/f'start-{i}';out.mkdir();shutil.copytree(source/'package',out/'package',copy_function=shutil.copyfile)
    for name in names:shutil.copyfile(source/name,out/name)
    for name in ('pose_live_pipeline_check','pose_display_worker'): (out/name).chmod(0o700)
    (out/'gates').mkdir()
    for gate in ('build','host-check','process-three'):shutil.copyfile(source/'gates'/f'{gate}.acceptance.json',out/'gates'/f'{gate}.acceptance.json')
    assert all(sha(out/name)==sha(source/name) for name in names)
(root/'planned-starts.json').write_text(json.dumps(dict(starts=3,program_sha256=sha(source/'pose_live_pipeline_check'),package_manifest_sha256=sha(source/'package/manifest.json'),Host_reused=True,stop_on_first_failure=True,no_automatic_retry=True))+'\n')
print('Three fresh starts prepared; no device opened')
