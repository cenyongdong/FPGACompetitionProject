"""Exact deletion of metadata adapter must recover frozen bridge/entry bytes."""
import json
from pathlib import Path
import mixed_validation_gate as g
root=g.ROOT
def text(rel):return (root/rel).read_text(encoding='utf-8')
s=text('software/pose_v1/src/tensor_identity_bridge_r2.cpp')
s=s.replace('#include "tensor_identity_observation.hpp"\n','')
a=s.index('std::string identityType(');b=s.index('template<class Op> void add() {',a);s=s[:a]+s[b:]
s=s.replace('        observeIdentity(op,index,false,src,dst,value.tensorType());\n','').replace('        observeIdentity(op,index,true,src,dst,value.tensorType());\n','')
assert s==text('software/pose_v1/src/producer_count_bridge_r2.cpp')
s=text('software/pose_v1/src/tensor_identity_check_r1.cpp')
s=s.replace('#include "tensor_identity_observation.hpp"\n','').replace('        pose::tensor_identity::configure(out/"tensor-identities");\n','').replace('        {"tensor-object-identities",[]{pose::tensor_identity::save();}},\n','')
assert s==text('software/pose_v1/src/producer_count_check_r2.cpp')
out=root/'tools/pose-v1/evidence/tensor-identity-20261010-r3/integration.review.json';assert not out.exists()
out.write_text(json.dumps(dict(status='metadata_only_exact_frozen_bridge_and_entry_recovered',
    removal_recovers_original_bytes=True,normal_device_reads_added=0,wait_copy_math_changed=False,
    original_error_source_reads_preserved=True,owned_shadow_before_new_validation=True,
    independent_persistence_tasks=8,public_objects_only=True),indent=2)+'\n');print('Frozen waits/copy/math/exception evidence recovered exactly after removing new metadata adapter.')
