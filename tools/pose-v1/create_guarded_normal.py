"""Explicit longer positive control; preserve the16s pressure fixture and failure."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'software/pose_v1/src/rtsp_guarded_normal_check.cpp';assert not target.exists()
s=(root/'software/pose_v1/src/rtsp_pressure_check.cpp').read_text(encoding='utf-8')
s=s.replace('Transport-only negative gate','Transport-only positive control').replace('--allow-network-pressure-test','--allow-network-control-test')
s=s.replace('options.maximumSeconds=20','options.maximumSeconds=35').replace('produced<160','produced<300')
s=s.replace('EXPECTED STOP: ','UNEXPECTED STOP: ').replace('Pressure did not trigger rejection','Normal reader control completed')
target.write_bytes(s.encode())
builder=root/'tools/pose-v1/Build-GuardedNormal.ps1';assert not builder.exists()
s=(root/'tools/pose-v1/Build-RtspPressure.ps1').read_text(encoding='utf-8')
s=s.replace('rtsp-pressure-20261008-r1','guarded-normal-20261008-r1').replace("'^rtsp-pressure-","'^guarded-normal-")
s=s.replace('rtsp_pressure_check.cpp','rtsp_guarded_normal_check.cpp').replace('pose_rtsp_pressure_check','pose_rtsp_guarded_normal_check')
builder.write_bytes(s.encode());print(target,builder)
