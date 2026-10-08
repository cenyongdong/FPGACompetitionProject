"""Explicit30-second normal control with the same guarded module and actual seed."""
import argparse,json,hashlib,shutil
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=Path(__file__).resolve().parents[2]
b=json.loads((a.build/'build-result.json').read_text(encoding='utf-8-sig'));assert not a.output.exists()
for rel,h in b['sources'].items():assert sha(root/rel)==h==sha(a.build/Path(rel).name)
negative=json.loads((root/'.local/pose-v1-build/rtsp-pressure-20261008-r1/build-result.json').read_text(encoding='utf-8-sig'))
assert all(b['sources'][rel]==negative['sources'][rel] for rel in b['sources'] if rel.endswith(('guarded_rtsp.cpp','guarded_rtsp.hpp','h264_access_unit.cpp','access_unit_channel.cpp')))
a.output.mkdir(parents=True);seed=root/'.local/pose-v1-pressure/package-20261008-r1'
for name in ['video.h264','packets.tsv','board_application_preflight.py']:shutil.copyfile(seed/name,a.output/name)
shutil.copyfile(a.build/'pose_rtsp_guarded_normal_check',a.output/'pose_rtsp_guarded_normal_check')
s=(root/'tools/pose-v1/run-rtsp-pressure.sh').read_text(encoding='utf-8').replace('run-pressure','run-normal').replace('pose_rtsp_pressure_check','pose_rtsp_guarded_normal_check').replace('--allow-network-pressure-test','--allow-network-control-test').replace('23s','38s').replace('PRESSURE_READY','NORMAL_READY').replace('Pressure program exit=','Normal control exit=')
(a.output/'run-normal.sh').write_bytes(s.encode())
m=dict(scope='SDK_free_guarded_normal_reader_control',frames=300,maximum_seconds=38,program_sha256=sha(a.output/'pose_rtsp_guarded_normal_check'),sources=b['sources'],guarded_module_same_negative=True,seed_sha256=sha(a.output/'video.h264'))
(a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode());(a.output/'files.sha256').write_bytes(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(a.output.iterdir()) if f.name!='files.sha256').encode());print('Prepared30s guarded normal control',a.output)
