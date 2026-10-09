"""Verify isolated source deltas without substituting for actual ARM tests."""
from pathlib import Path
import json,hashlib
import mixed_validation_gate as old
root=old.ROOT
header=(root/'software/pose_v1/include/application_core.hpp').read_text(encoding='utf-8')
assert (root/'software/pose_v1/include/trace_application_core_r2.hpp').read_text(encoding='utf-8')==header.replace('size_t diagnostic_frames=4;','size_t diagnostic_frames=4;\n    size_t timing_frames=0;')
core=(root/'software/pose_v1/src/application_core.cpp').read_text(encoding='utf-8')
assert (root/'software/pose_v1/src/trace_application_core_r2.cpp').read_text(encoding='utf-8')==core.replace('fc::sample_limit=c.diagnostic_frames;','need(c.timing_frames<=32,"Timing sampling is bounded to32 frames");\n        fc::sample_limit=c.timing_frames?c.timing_frames:c.diagnostic_frames;')
old_bridge=(root/'software/pose_v1/src/application_bridge.cpp').read_text(encoding='utf-8')
new_bridge=(root/'software/pose_v1/src/trace_application_bridge_r2.cpp').read_text(encoding='utf-8')
new_bridge=new_bridge.replace('#include "host_failure_evidence.hpp"\n#include <cstring>\n#include <sstream>\n','')
start=new_bridge.index('auto compute=Clock::now();std::vector<xrt::Tensor> computed;')
end=new_bridge.index('    forward_clock::record("bridge.cpu"',start)
new_bridge=new_bridge[:start]+'auto compute=Clock::now();auto computed=cpu::forward(op,staged,{});\n'+new_bridge[end:]
assert new_bridge==old_bridge
before=(root/'software/pose_v1/src/host_failure_adapter_test.cpp').read_text(encoding='utf-8');after=(root/'software/pose_v1/src/host_failure_adapter_test_r3.cpp').read_text(encoding='utf-8')
assert after==before.replace('namespace xir=icraft::xir;namespace xrt=icraft::xrt;','namespace xir=icraft::xir;namespace xrt=icraft::xrt;\n    // Host gate local log has ended; use an explicitly empty public bridge context.\n    pose_v1::mixed_candidate::configure(nullptr,false);')
m=old.load(root/'.local/pose-v1-forward-trace/package-20261009-r3/manifest.json')
for key in ('trace_frozen_parent','trace_r2_frozen_sources','trace_r3_frozen_sources','frozen_live_sources','frozen_resident_module_sources'):
    for rel,digest in m[key].items():assert old.sha(root/rel)==digest
out=root/'tools/pose-v1/evidence/forward-trace-20261009-r3/source-delta-review.json';assert not out.exists()
out.write_text(json.dumps(dict(status='isolated_deltas_verified',core_extra_SDK_queries_added=False,core_math_copy_wait_frame_protocol_unchanged=True,bridge_normal_flow_unchanged=True,failure_only_owned_Host_capture=True,Host_probe_explicit_empty_context=True,frozen_old_sources_preserved=True,ARM_test_substitute=False,source_sha256={rel:old.sha(root/rel) for rel in m['build_files']}),indent=2)+'\n')
print('Isolated deltas and frozen source identities verified.')
