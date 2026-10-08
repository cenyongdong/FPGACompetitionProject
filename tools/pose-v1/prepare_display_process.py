"""Freeze r2 baseline and add only isolated process modules and validation tooling."""
import argparse,json,shutil
from pathlib import Path
import mixed_validation_gate as old

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    root=old.ROOT;base=root/'.local/pose-v1-system-timing/package-20261008-r2';old.verify(base);m=old.load(base/'manifest.json')
    for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
    for rel,digest in m['sources'].items():assert old.sha(root/rel)==digest
    removed=('software/pose_v1/src/system_timing_check.cpp','software/pose_v1/src/timed_window_input.cpp','tools/pose-v1/system-timing-CMakeLists.txt')
    m['display_frozen_parent']={rel:old.sha(root/rel) for rel in removed}
    for rel in removed:del m['build_files'][rel]
    names=('src/display_process_check.cpp','src/process_system_timing.cpp','src/process_window_input.cpp','include/process_window_input.hpp','include/display_protocol.hpp','src/display_protocol.cpp','include/display_process.hpp','src/display_process.cpp','include/display_queue.hpp','src/display_worker.cpp','src/display_process_selftest.cpp')
    for name in names:
        rel='software/pose_v1/'+name;m['build_files'][rel]=dict(destination=Path(name).name,sha256=old.sha(root/rel))
    rel='tools/pose-v1/display-process-CMakeLists.txt';m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=old.sha(root/rel))
    for name in ('prepare_display_process.py','Build-DisplayProcess.ps1','create_display_process_target.py','run-display-process.sh','display_process_peer.py','review_display_process.py'):
        rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
    m['build_script']='tools/pose-v1/Build-DisplayProcess.ps1';m['display_process']=dict(exec_before_parent_devices=True,SDK_in_child=False,IPC='AF_UNIX SOCK_STREAM exact bounded messages',queue_capacity=2,IPC_credit=1,reply_bytes=1280*720*3//2,shared_mutable_memory=False)
    m['scope']='Separate SDK-free display executable, explicit IPC owned copies, main-owned Engine unchanged'
    shutil.copytree(base,a.output);(a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    (a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
    print(json.dumps(dict(payloads=old.verify(a.output),build_sources=len(m['build_files']),manifest_sha256=old.sha(a.output/'manifest.json'))))
if __name__=='__main__':main()
