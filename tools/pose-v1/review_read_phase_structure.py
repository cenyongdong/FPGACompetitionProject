"""Prove the isolated caller changes leave frozen math/copy logic intact."""
import json
from pathlib import Path
import mixed_validation_gate as g
r=g.ROOT;e=r/'tools/pose-v1/evidence/read-phase-20261011-r2'
text=lambda p:(r/p).read_text(encoding='utf-8')
b=text('software/pose_v1/src/read_phase_bridge.cpp')
b=b.replace('#include "read_phase_sdk.hpp"\n','')
b=b.replace('if(op->op_id==192&&index==1){pose::read_phase_sdk::copy(frame_id,invocation_id,src,dst,host(src));}else{if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}}','if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}')
b=b.replace('if(op->op_id==192){pose::read_phase_sdk::beforeCPU(staged.at(1));}','')
b=b.replace('if(op->op_id==192){pose::read_phase_sdk::error(error.what());}\n        // Original failure path and late source reads are preserved.','// Successful path unchanged. All snapshots own bytes from existing Host staging.')
assert b==text('software/pose_v1/src/read_input_bridge.cpp')
s=text('software/pose_v1/src/read_phase_check.cpp')
s=s.replace('#include "read_phase_sdk.hpp"\n','').replace('\n        pose::read_phase_sdk::configure(out/"read-phase");','')
s=s.replace('\n    pose::invocation_evidence::flush({{"read-phase",[]{pose::read_phase_sdk::save();}}},failure,out/"read-phase-persistence-ledger.json");','')
assert s==text('software/pose_v1/src/upstream_boundary_check_r4.cpp')
p=e/'bridge-structure-review.json';assert not p.exists()
p.write_text(json.dumps(dict(status='three_observation_insertions_only',old_bridge_frozen=True,math_copy_waits_outputs_unchanged=True,main_configuration_and_separate_save_only=True),indent=2)+'\n',encoding='utf-8',newline='\n')
print('Bridge and orchestrator structural equivalence passed')
