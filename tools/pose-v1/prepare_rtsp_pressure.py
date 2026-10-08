"""Package pinned seed NALs and guarded network candidate; no devices."""
import argparse,json,hashlib,shutil
from pathlib import Path
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];build=json.loads((a.build/'build-result.json').read_text(encoding='utf-8-sig'));assert not a.output.exists()
for rel,h in build['sources'].items():assert sha(root/rel)==h==sha(a.build/Path(rel).name)
assert 'error:' not in (a.build/'build.log').read_text() and 'warning:' not in (a.build/'build.log').read_text()
seed=root/'.local/pose-v1-owned-rtsp/package-20261008-r3-final';seedm=json.loads((seed/'manifest.json').read_text());assert sha(seed/'video.h264')==seedm['capture_sha256']
a.output.mkdir(parents=True)
for name in ['video.h264','packets.tsv']:shutil.copyfile(seed/name,a.output/name)
shutil.copyfile(a.build/'pose_rtsp_pressure_check',a.output/'pose_rtsp_pressure_check')
assert sha(a.output/'pose_rtsp_pressure_check')==build['programs']['pose_rtsp_pressure_check']
for name in ['board_application_preflight.py','run-rtsp-pressure.sh']:shutil.copyfile(root/'tools/pose-v1'/name,a.output/name)
(a.output/'manifest.json').write_bytes((json.dumps(dict(scope='SDK_free_slow_reader_negative_gate',program_sha256=sha(a.output/'pose_rtsp_pressure_check'),sources=build['sources'],vendor_files=build['vendor_files'],seed_hash=sha(a.output/'video.h264'),tcp_send_buffer=65536,expected='send_error_stop_no_VPU_NPU'),indent=2)+'\n').encode())
(a.output/'files.sha256').write_bytes(''.join(sha(f)+'  '+f.name+'\n' for f in sorted(a.output.iterdir()) if f.name!='files.sha256').encode())
print('Prepared guarded SDK-free pressure package',a.output)
