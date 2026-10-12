"""Correct the new target's bridge wiring; preserve r2 and all frozen observations."""
import json,shutil
import mixed_validation_gate as g
r=g.ROOT;prior=r/'.local/pose-v1-read-phase/package-20261011-r2';g.verify(prior);m=g.load(prior/'manifest.json')
m['read_phase_r2_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
def once(s,a,b):assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def fresh(p,s):assert not (r/p).exists();(r/p).write_text(s,encoding='utf-8',newline='\n')
bridge=(r/'software/pose_v1/src/final_evidence_bridge.cpp').read_text(encoding='utf-8')
bridge=once(bridge,'#include "input_read_sdk.hpp"','#include "input_read_sdk.hpp"\n#include "read_phase_sdk.hpp"')
original='if(host(src)){dst.copyFrom(0,src,0,value.tensorType().bytes());}else{pose::input_read::intoHost(src,dst);}'
bridge=once(bridge,original,'if(op->op_id==192&&index==1){pose::read_phase_sdk::copy(frame_id,invocation_id,src,dst,host(src));}else{'+original+'}')
bridge=once(bridge,'try{observation.validate();computed=cpu::forward(op,staged,{});}','try{observation.validate();if(op->op_id==192){pose::read_phase_sdk::beforeCPU(staged.at(1));}computed=cpu::forward(op,staged,{});}')
bridge=once(bridge,'// Successful path unchanged. All snapshots own bytes from existing Host staging.','if(op->op_id==192){pose::read_phase_sdk::error(error.what());}\n        // Original failure path and late source reads are preserved.')
new='software/pose_v1/src/read_phase_bridge_r3.cpp';fresh(new,bridge)
m['build_files'].pop('software/pose_v1/src/read_phase_bridge.cpp');m['build_files'][new]=dict(destination='read_phase_bridge.cpp',sha256=g.sha(r/new))
cm=(r/'tools/pose-v1/read-phase-CMakeLists.txt').read_text(encoding='utf-8');start=cm.index('add_executable(pose_read_phase_check ');end=cm.index('target_include_directories(pose_read_phase_check',start)
block=once(cm[start:end],'final_evidence_bridge.cpp','read_phase_bridge.cpp');assert 'read_input_bridge.cpp' not in block and block.count('read_phase_bridge.cpp')==1
cm=cm[:start]+block+cm[end:];new='tools/pose-v1/read-phase-r3-CMakeLists.txt';fresh(new,cm)
m['build_files'].pop('tools/pose-v1/read-phase-CMakeLists.txt');m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(r/new))
base='tools/pose-v1/review_read_phase_r2_build_base.py';new='tools/pose-v1/review_read_phase_r3_build_base.py';text=(r/base).read_text(encoding='utf-8').replace("'read_phase_r1_frozen_sources')","'read_phase_r1_frozen_sources','read_phase_r2_frozen_sources')")
marker='    return m,b,n';guard='''    cm=(build/'source/CMakeLists.txt').read_text(encoding='utf-8')
    block=cm[cm.index('add_executable(pose_read_phase_check '):cm.index('target_include_directories(pose_read_phase_check')]
    assert block.count('read_phase_bridge.cpp')==1 and 'final_evidence_bridge.cpp' not in block and 'read_input_bridge.cpp' not in block
    assert 'CMakeFiles/pose_read_phase_check.dir/read_phase_bridge.cpp.o' in log
'''
text=once(text,marker,guard+marker);fresh(new,text)
base='tools/pose-v1/review_read_phase_r2_stage.py';new='tools/pose-v1/review_read_phase_r3_stage.py';fresh(new,(r/base).read_text(encoding='utf-8').replace('review_read_phase_r2_build_base','review_read_phase_r3_build_base'))
for name in ['prepare_read_phase_r3.py','review_read_phase_r3_build_base.py','review_read_phase_r3_stage.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(r/rel)
m['read_phase']['r2_failure']='four60400 correct, no observer wiring, independent save refused empty; preserved; no highload'
m['read_phase']['actual_bridge']='frozen final_evidence bridge plus three observation sites, explicitly linked'
out=r/'.local/pose-v1-read-phase/package-20261011-r3';assert not out.exists();shutil.copytree(prior,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
