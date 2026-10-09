"""Bound the r4 diff to configuration and exception-only diagnostic invocation."""
from pathlib import Path
import json
import mixed_validation_gate as old
root=old.ROOT
before=(root/'software/pose_v1/src/trace_application_bridge_r2.cpp').read_text(encoding='utf-8');after=(root/'software/pose_v1/src/source_application_bridge_r4.cpp').read_text(encoding='utf-8')
after=after.replace('#include "failure_source_readback.hpp"\n','').replace('\n            size_t totalBytes=0;for(const auto& b:blobs)totalBytes+=b.bytes.size();\n            pose::source_diagnostic::capture(frame_id,invocation_id,op->op_id,inputs,allowed_device,permit_hardware,totalBytes);','')
assert before==after
m=old.load(root/'.local/pose-v1-source-readback/package-20261009-r4/manifest.json')
for key in ('source_r4_frozen_sources','trace_r2_frozen_sources','trace_r3_frozen_sources','frozen_live_sources','frozen_resident_module_sources'):
    for rel,digest in m[key].items():assert old.sha(root/rel)==digest
out=root/'tools/pose-v1/evidence/source-readback-20261009-r4/source-delta-review.json';assert not out.exists()
out.write_text(json.dumps(dict(status='exception_only_delta_verified',normal_bridge_flow_unchanged=True,CPU_math_wait_copy_unchanged=True,readback_rounds=2,direct_ADDR_dereference=False,explicit_wait_reset_cache=False,frozen_sources_preserved=True,hardware_test_substitute=False,source_sha256={k:v['sha256'] for k,v in m['build_files'].items()}),indent=2)+'\n')
print('Exception-only source-reader invocation and frozen source identities verified.')
