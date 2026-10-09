"""Exact new r2 archive; preserves r1 transfer and all returned evidence."""
from pathlib import Path
import shutil,tarfile
import mixed_validation_gate as old
root=old.ROOT;base=root/'.local/pose-v1-forward-trace';out=base/'transfer-20261009-r2';assert not out.exists();out.mkdir()
shutil.copytree(base/'package-20261009-r2',out/'package');build=root/'.local/pose-v1-build/mixed-20261009-forward-trace-r2'
for name in ('pose_access_unit_selftest','pose_tcp_transport_check','pose_failed_result_selftest','pose_system_timing_selftest','pose_display_worker','pose_display_process_selftest','pose_failure_evidence_selftest','build-result.json'):shutil.copyfile(build/name,out/name)
shutil.copyfile(build/'pose_live_pipeline_check.arm64',out/'pose_live_pipeline_check')
for name in ('run-forward-trace-r2.sh','board_application_preflight.py','compact_once_evidence.py'):shutil.copyfile(root/'tools/pose-v1'/name,out/name)
(out/'gates').mkdir();shutil.copyfile(root/'tools/pose-v1/evidence/forward-trace-20261009-r2/build.acceptance.json',out/'gates/build.acceptance.json')
archive=base/'transfer-20261009-r2.tar';assert not archive.exists()
with tarfile.open(archive,'w') as f:
    for p in sorted(out.iterdir()):f.add(p,arcname=p.name)
print(archive)
