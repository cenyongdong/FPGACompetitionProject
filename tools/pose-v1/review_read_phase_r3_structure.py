"""Compare against the actual frozen bridge and verify its target wiring."""
import json
import mixed_validation_gate as g
r=g.ROOT;e=r/'tools/pose-v1/evidence/read-phase-20261011-r3'
text=lambda p:(r/p).read_text(encoding='utf-8')
b=text('software/pose_v1/src/read_phase_bridge_r3.cpp').replace('#include "read_phase_sdk.hpp"\n','')
b=b.replace('if(op->op_id==192&&index==1){pose::read_phase_sdk::copy(frame_id,invocation_id,src,dst,host(src));}else{if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}}','if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}')
b=b.replace('if(op->op_id==192){pose::read_phase_sdk::beforeCPU(staged.at(1));}','')
b=b.replace('if(op->op_id==192){pose::read_phase_sdk::error(error.what());}\n        // Original failure path and late source reads are preserved.','// Successful path unchanged. All snapshots own bytes from existing Host staging.')
assert b==text('software/pose_v1/src/final_evidence_bridge.cpp')
s=text('software/pose_v1/src/read_phase_check.cpp').replace('#include "read_phase_sdk.hpp"\n','').replace('\n        pose::read_phase_sdk::configure(out/"read-phase");','')
s=s.replace('\n    pose::invocation_evidence::flush({{"read-phase",[]{pose::read_phase_sdk::save();}}},failure,out/"read-phase-persistence-ledger.json");','')
assert s==text('software/pose_v1/src/upstream_boundary_check_r4.cpp')
cm=text('tools/pose-v1/read-phase-r3-CMakeLists.txt');block=cm[cm.index('add_executable(pose_read_phase_check '):cm.index('target_include_directories(pose_read_phase_check')]
assert block.count('read_phase_bridge.cpp')==1 and 'final_evidence_bridge.cpp' not in block and 'read_input_bridge.cpp' not in block
assert all(t in b for t in ['pose::final_source_sdk::begin','pose::final_source_sdk::source','pose::final_source_sdk::outputs'])
p=e/'bridge-structure-review.json';assert not p.exists();p.write_text(json.dumps(dict(status='actual_bridge_three_observation_sites_and_target_wiring_verified',actual_parent='final_evidence_bridge.cpp',math_copy_wait_output_unchanged=True,final_source_capture_preserved=True,main_configuration_separate_save_only=True),indent=2)+'\n',encoding='utf-8',newline='\n');print('Actual frozen bridge and target wiring verified')
