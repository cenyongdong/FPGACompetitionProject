"""Freeze one transfer, retaining package and all binary identities."""
import shutil,tarfile
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-plddr-position';build=root/'.local/pose-v1-build/mixed-20261010-plddr-position-r1';out=base/'transfer-20261010-r1';assert not out.exists();out.mkdir()
shutil.copytree(base/'package-20261010-r1',out/'package')
for name in ('pose_position_scratch_check','pose_plddr_position_selftest','pose_typed_scratch_selftest','build-result.json'):shutil.copyfile(build/name,out/name)
shutil.copyfile(build/'pose_live_pipeline_check.arm64',out/'pose_live_pipeline_check')
for name in ('board_application_preflight.py','run-position-scratch.sh','compact_typed_before_vpu.py'):shutil.copyfile(root/'tools/pose-v1'/name,out/name)
e=root/'tools/pose-v1/evidence/plddr-position-20261010-r1';shutil.copyfile(e/'manager.acceptance.json',out/'manager.acceptance.json');(out/'gates').mkdir();shutil.copyfile(e/'baseline.acceptance.json',out/'gates/baseline.acceptance.json')
archive=base/'transfer-20261010-r1.tar';assert not archive.exists()
with tarfile.open(archive,'w') as f:
    for p in sorted(out.iterdir()):f.add(p,arcname=p.name)
print(archive,g.sha(archive))
