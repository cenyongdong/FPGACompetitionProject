"""Stage the new resident lifecycle without overwriting any prior candidate."""
import shutil,tarfile
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-resident-sequence';build=root/'.local/pose-v1-build/mixed-20261010-resident-sequence-r1';out=base/'transfer-20261010-r1';assert not out.exists();out.mkdir()
shutil.copytree(base/'package-20261010-r1',out/'package')
for name in ['pose_resident_sequence_check','pose_resident_sequence_selftest','pose_resident_producer_selftest','pose_model_load_selftest','pose_model_only_selftest','build-result.json']:shutil.copyfile(build/name,out/name)
shutil.copyfile(build/'pose_live_pipeline_check.arm64',out/'pose_live_pipeline_check')
for name in ['board_application_preflight.py','run-resident-sequence.sh','compact_typed_before_vpu.py']:shutil.copyfile(root/'tools/pose-v1'/name,out/name)
(out/'gates').mkdir();shutil.copyfile(root/'tools/pose-v1/evidence/resident-sequence-20261010-r1/baseline.acceptance.json',out/'gates/baseline.acceptance.json')
archive=base/'transfer-20261010-r1.tar';assert not archive.exists()
with tarfile.open(archive,'w') as f:
    for item in sorted(out.iterdir()):f.add(item,arcname=item.name)
print(archive,g.sha(archive))
