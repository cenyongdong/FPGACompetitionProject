"""Explicit package/build identities, preserve prior archives."""
import argparse,json,shutil,tarfile
from pathlib import Path
import mixed_validation_gate as g
p=argparse.ArgumentParser()
for key in ['package','build','gate','output','archive']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();assert not a.output.exists() and not a.archive.exists();g.verify(a.package)
b=g.load(a.build/'build-result.json');gate=g.load(a.gate)
assert b['stage']=='compiled_not_executed' and b['package_manifest_sha256']==g.sha(a.package/'manifest.json')==gate['package_manifest_sha256']
assert gate['binary_sha256']==b['phase_binary_sha256']==g.sha(a.build/'pose_read_phase_check')
for name,key in [('pose_read_phase_sdk_selftest','phase_sdk_contract_sha256'),('pose_read_phase_selftest','phase_contract_sha256'),('pose_upstream_boundary_selftest','upstream_contract_sha256'),('pose_upstream_boundary_sdk_selftest','upstream_sdk_contract_sha256')]:assert g.sha(a.build/name)==b[key]
a.output.mkdir();shutil.copytree(a.package,a.output/'package')
names=['pose_read_phase_check','pose_display_worker','pose_display_process_selftest','pose_access_unit_selftest','pose_tcp_transport_check','pose_failed_result_selftest','pose_system_timing_selftest','pose_failure_evidence_selftest','pose_bounded_load_selftest','pose_stage_observation_selftest','pose_invocation_evidence_selftest','pose_producer_count_selftest','pose_tensor_identity_selftest','pose_final_source_selftest','pose_final_source_sdk_selftest','pose_upstream_boundary_selftest','pose_upstream_boundary_sdk_selftest','pose_read_phase_selftest','pose_read_phase_sdk_selftest','build-result.json']
for name in names:shutil.copyfile(a.build/name,a.output/name)
for name in ['board_application_preflight.py','run-read-phase.sh','compact_typed_before_vpu.py']:shutil.copyfile(g.ROOT/'tools/pose-v1'/name,a.output/name)
(a.output/'gates').mkdir();shutil.copyfile(a.gate,a.output/'gates/build.acceptance.json')
identity=dict(package=str(a.package.resolve()),build=str(a.build.resolve()),manifest_SHA256=b['package_manifest_sha256'],binary_SHA256=b['phase_binary_sha256'],SDK_contract_SHA256=b['phase_sdk_contract_sha256'],script_SHA256=g.sha(Path(__file__)))
(a.output/'transfer-identity.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8',newline='\n')
def metadata(info):
    info.mtime=0
    # Preserve executable deployment metadata for future new archives.
    if info.isfile() and Path(info.name).name.startswith('pose_'):info.mode=0o755
    return info
with tarfile.open(a.archive,'w') as f:
    for item in sorted(a.output.iterdir()):f.add(item,arcname=item.name,filter=metadata)
print(a.archive,g.sha(a.archive))
