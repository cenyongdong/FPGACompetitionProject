"""Freeze existing payloads and isolate orchestration/log-only timing copies."""
import argparse,json,shutil
from pathlib import Path
import mixed_validation_gate as old

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    root=old.ROOT;base=root/'.local/pose-v1-tcp-presaved/package-20261008-r1';old.verify(base);m=old.load(base/'manifest.json')
    for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
    for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
    removed=('software/pose_v1/src/live_tcp_presaved_check.cpp','software/pose_v1/src/tcp_window_input.cpp','software/pose_v1/src/vpu_resident_encoder.cpp','software/pose_v1/src/guarded_rtsp.cpp','tools/pose-v1/tcp-presaved-CMakeLists.txt')
    m['timing_frozen_parent']={rel:old.sha(root/rel) for rel in removed}
    for rel in removed:del m['build_files'][rel]
    for name in ('src/system_timing_check.cpp','src/system_timing.cpp','src/system_timing_selftest.cpp','src/timed_window_input.cpp','src/timed_resident_encoder.cpp','src/timed_guarded_rtsp.cpp','include/system_timing.hpp','include/timed_window_input.hpp'):
        rel='software/pose_v1/'+name;m['build_files'][rel]=dict(destination=Path(name).name,sha256=old.sha(root/rel))
    rel='tools/pose-v1/system-timing-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=old.sha(root/rel))
    for name in ('prepare_system_timing.py','Build-SystemTiming.ps1','create_system_timing.py','run-system-timing.sh','system_timing_peer.py','review_system_timing.py'):
        rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
    m['build_script']='tools/pose-v1/Build-SystemTiming.ps1';m['system_timing']=dict(clock='std::chrono::steady_clock',warmups=3,sent=33,transport_id_base=100000,receiver_capacity=1,frame_capacity=2,AU_capacity=8,ordinary_compaction_allowed=False)
    m['scope']='Isolated whole-system timing; owned complete outputs persist after workers join; frozen math/copies/IOCTLs/SDK completion'
    shutil.copytree(base,a.output);(a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    (a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
    print(json.dumps(dict(payloads=old.verify(a.output),build_sources=len(m['build_files']),manifest_sha256=old.sha(a.output/'manifest.json'))))
if __name__=='__main__':main()
