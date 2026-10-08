"""SDK-independent guarded transport test build; keep accepted builders intact."""
from pathlib import Path
root=Path(__file__).resolve().parents[2];target=root/'tools/pose-v1/Build-RtspPressure.ps1';assert not target.exists()
s=(root/'tools/pose-v1/Build-OwnedRtsp.ps1').read_text(encoding='utf-8')
s=s.replace('owned-rtsp-20261008-r1','rtsp-pressure-20261008-r1').replace("'^owned-rtsp-","'^rtsp-pressure-")
s=s.replace("'include/online_rtsp.hpp',","'include/online_rtsp.hpp','include/guarded_rtsp.hpp',")
s=s.replace('src/online_rtsp.cpp','src/guarded_rtsp.cpp').replace('src/owned_rtsp_check.cpp','src/rtsp_pressure_check.cpp')
s=s.replace('/online_rtsp.cpp','/guarded_rtsp.cpp').replace('/owned_rtsp_check.cpp','/rtsp_pressure_check.cpp')
s=s.replace('pose_owned_rtsp_check','pose_rtsp_pressure_check')
target.write_bytes(s.encode());print(target)
