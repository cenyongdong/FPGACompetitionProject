"""Fresh complete-window TCP/guarded RTSP integration package."""
import argparse,json,shutil
from pathlib import Path
import mixed_validation_gate as old
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    root=old.ROOT;base=root/'.local/pose-v1-guarded-live/package-20261008-r1';old.verify(base);m=old.load(base/'manifest.json')
    for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
    for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
    for rel in ('software/pose_v1/src/live_pipeline_check.cpp','tools/pose-v1/guarded-live-CMakeLists.txt'):del m['build_files'][rel]
    for name in ('src/live_tcp_pipeline_check.cpp','include/tcp_window_input.hpp','src/tcp_window_input.cpp','include/tcp_receiver.hpp','src/tcp_receiver.cpp','src/tcp_transport_check.cpp'):
        rel='software/pose_v1/'+name;m['build_files'][rel]=dict(destination=Path(name).name,sha256=old.sha(root/rel))
    rel='tools/pose-v1/tcp-live-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=old.sha(root/rel))
    for name in ('prepare_tcp_live.py','Build-TcpLive.ps1','run-tcp-live.sh','send_live_windows.py','create_tcp_live_target.py'):
        rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
    m['build_script']='tools/pose-v1/Build-TcpLive.ps1';m['tcp_window_input']=True
    m['scope']='owned complete-window TCP to main-owned Engine/render/VPU/guarded RTSP; finite2Hz diagnostic only'
    baseline=old.load(root/'.local/pose-v1-build/mixed-20261007-application-r2/build-result.json')
    for rel in ('software/pose_v1/include/tcp_receiver.hpp','software/pose_v1/src/tcp_receiver.cpp','software/pose_v1/src/tcp_transport_check.cpp'):
        assert m['build_files'][rel]['sha256']==baseline['source_sha256'][rel]
    shutil.copytree(base,a.output)
    (a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    (a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
    print(json.dumps(dict(payloads=old.verify(a.output),build_sources=len(m['build_files']),manifest_sha256=old.sha(a.output/'manifest.json'))))
if __name__=='__main__':main()
