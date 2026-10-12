"""Package reviewed independent composition, with epoch transfer metadata."""
import shutil,tarfile
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-upstream-boundary';build=root/'.local/pose-v1-build/mixed-20261011-upstream-boundary-r1';out=base/'transfer-20261011-r1';assert not out.exists();out.mkdir()
shutil.copytree(base/'package-20261011-r1',out/'package')
names=['pose_upstream_boundary_check','pose_display_worker','pose_display_process_selftest','pose_access_unit_selftest','pose_tcp_transport_check','pose_failed_result_selftest','pose_system_timing_selftest','pose_failure_evidence_selftest','pose_bounded_load_selftest','pose_stage_observation_selftest','pose_invocation_evidence_selftest','pose_producer_count_selftest','pose_tensor_identity_selftest','pose_final_source_selftest','pose_final_source_sdk_selftest','pose_upstream_boundary_selftest','pose_upstream_boundary_sdk_selftest','build-result.json']
for name in names:shutil.copyfile(build/name,out/name)
for name in ['board_application_preflight.py','run-upstream-boundary.sh','compact_typed_before_vpu.py']:shutil.copyfile(root/'tools/pose-v1'/name,out/name)
(out/'gates').mkdir();shutil.copyfile(root/'tools/pose-v1/evidence/upstream-boundary-20261011-r1/build.acceptance.json',out/'gates/build.acceptance.json')
archive=base/'transfer-20261011-r1.tar';assert not archive.exists()
def metadata(info):info.mtime=0;return info
with tarfile.open(archive,'w') as f:
    for item in sorted(out.iterdir()):f.add(item,arcname=item.name,filter=metadata)
print(archive,g.sha(archive))
