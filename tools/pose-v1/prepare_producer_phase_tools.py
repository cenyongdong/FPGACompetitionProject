"""Prepare separate bounded build/execution scripts; do not run old hardware stages."""
from pathlib import Path
R = Path(__file__).resolve().parents[2]
T = R / 'tools/pose-v1'

def put(name, s):
    p = T / name
    assert not p.exists()
    p.write_text(s, encoding='utf-8', newline='\n')

s = (T / 'build_producer_vpu_r2.py').read_text()
s = s.replace('producer-vpu-', 'producer-phase-').replace("tag='20261011-r2'", "tag='20261011-r1'")
s = s.replace("'producer_sdk.cpp','producer_vpu_check.cpp'", "'producer_phase_sdk.cpp','producer_phase_check.cpp','producer_phase_trace.cpp','producer_phase_selftest.cpp'")
s = s.replace("'observer':['vpu_ioctl_observation.cpp','vpu_ioctl_observation_selftest.cpp']", "'observer':['vpu_ioctl_observation.cpp','vpu_ioctl_observation_selftest.cpp'],'phase':['producer_phase_trace.cpp','producer_phase_selftest.cpp']")
s = s.replace("([remote+'/observer-native'] if name=='observer' else [])", "([remote+'/'+name+'-native'] if name in ('observer','phase') else [])")
s = s.replace("'producer_payload.cpp','producer_sdk.cpp','producer_vpu_check.cpp'", "'producer_payload.cpp','producer_phase_sdk.cpp','producer_phase_check.cpp','producer_phase_trace.cpp'")
# Above source-list replacement must not accidentally include the selftest main in link objects.
s = s.replace("for n in ('producer_payload.cpp','producer_phase_sdk.cpp','producer_phase_check.cpp','producer_phase_trace.cpp','producer_phase_selftest.cpp',", "for n in ('producer_payload.cpp','producer_phase_sdk.cpp','producer_phase_check.cpp','producer_phase_trace.cpp',")
s = s.replace('pose_producer_vpu_check', 'pose_producer_phase_check')
s = s.replace("'board_producer_vpu_run.py'", "'board_producer_phase_run.py'")
s = s.replace('"""Build fixed100 off/on candidate with frozen SDK and VPU implementation."""', '"""Build isolated pre-reset diagnostic; frozen sources preserved."""')
put('build_producer_phase.py', s)

s = (T / 'board_producer_vpu_run.py').read_text().replace('pose_producer_vpu_check', 'pose_producer_phase_check')
s = s.replace("capture(['./pose_producer_observer_selftest',str(run/'observer')],'observer-arm.txt');", "capture(['./pose_producer_observer_selftest',str(run/'observer')],'observer-arm.txt');capture(['./pose_producer_phase_selftest',str(run/'phase')],'phase-arm.txt');")
put('board_producer_phase_run.py', s)

s = (T / 'execute_producer_vpu.py').read_text().replace('producer-vpu-20261011-r2', 'producer-phase-20261011-r1').replace('board_producer_vpu_run.py', 'board_producer_phase_run.py')
s = s.replace('pose_producer_vpu_check', 'pose_producer_phase_check')
s = s.replace('pose_producer_observer_selftest;', 'pose_producer_observer_selftest pose_producer_phase_selftest;')
s = s.replace("print('ARM payload/schedule/ioctl transparency passed; no device initialization')", "print('ARM payload/schedule/ioctl/phase contracts passed; no device initialization')")
put('execute_producer_phase.py', s)
s = (T / 'review_producer_vpu_outputs.py').read_text().replace('producer-vpu-20261011-r2', 'producer-phase-20261011-r1')
put('review_producer_phase_outputs.py', s)
# Restrict remote transfers to this new isolated task directory.
p = T / 'ssh_memory_transport.py'
s = p.read_text()
assert '/tmp/pose-producer-phase-20261011-r1/' not in s
p.write_text(s.replace("remote.startswith(('/tmp/pose-producer-vpu-", "remote.startswith(('/tmp/pose-producer-phase-20261011-r1/','/tmp/pose-producer-vpu-"), encoding='utf-8', newline='\n')
print('New phase build/manager/transport ready; hardware not executed')
