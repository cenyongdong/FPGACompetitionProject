"""Stage exact accepted build, package, runner and gates in a fresh archive."""
from pathlib import Path
import shutil, tarfile
import mixed_validation_gate as old
root=old.ROOT;base=root/'.local/pose-v1-forward-trace';out=base/'transfer-20261008-r1';assert not out.exists();out.mkdir()
shutil.copytree(base/'package-20261008-r1',out/'package')
build=root/'.local/pose-v1-build/mixed-20261008-forward-trace-r1'
for name in ('pose_access_unit_selftest','pose_tcp_transport_check','pose_failed_result_selftest','pose_system_timing_selftest','pose_display_worker','pose_display_process_selftest','build-result.json'):shutil.copyfile(build/name,out/name)
shutil.copyfile(build/'pose_live_pipeline_check.arm64',out/'pose_live_pipeline_check')
for source,dest in [('run-forward-trace.sh','run-forward-trace.sh'),('board_application_preflight.py','board_application_preflight.py'),('compact_once_evidence.py','compact_once_evidence.py')]:shutil.copyfile(root/'tools/pose-v1'/source,out/dest)
(out/'gates').mkdir();shutil.copyfile(root/'tools/pose-v1/evidence/forward-trace-20261008-r1/build.acceptance.json',out/'gates/build.acceptance.json')
archive=base/'transfer-20261008-r1.tar';assert not archive.exists()
with tarfile.open(archive,'w') as f:
    for p in sorted(out.iterdir()):f.add(p,arcname=p.name)
print(archive)
