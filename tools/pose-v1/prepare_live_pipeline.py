"""Fresh integration package; preserve verified module payloads and identities."""
import argparse,json,shutil,hashlib
from pathlib import Path
import mixed_validation_gate as old

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    root=old.ROOT;base=root/'.local/pose-v1-resident/package-20261008-r6';old.verify(base);m=old.load(base/'manifest.json')
    for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
    au=old.load(root/'.local/pose-v1-build/owned-rtsp-20261008-r3/build-result.json')
    for rel,h in au['sources'].items():assert old.sha(root/rel)==h
    m['build_files']={k:v for k,v in m['build_files'].items() if k not in ('software/pose_v1/src/resident_owner_check.cpp','tools/pose-v1/resident-CMakeLists.txt')}
    add=['include/pipeline_fixture_source.hpp','src/pipeline_fixture_source.cpp','include/video_frame_marker.hpp','src/live_host_gate.cpp','src/live_pipeline_check.cpp',
         'include/h264_access_unit.hpp','src/h264_access_unit.cpp','include/access_unit_channel.hpp','src/access_unit_channel.cpp','include/online_rtsp.hpp','src/online_rtsp.cpp','src/access_unit_selftest.cpp']
    for name in add:
        rel='software/pose_v1/'+name;m['build_files'][rel]=dict(destination=Path(name).name,sha256=old.sha(root/rel))
    m['build_files']['tools/pose-v1/live-CMakeLists.txt']=dict(destination='CMakeLists.txt',sha256=old.sha(root/'tools/pose-v1/live-CMakeLists.txt'))
    m['sources']={k:v for k,v in m['sources'].items() if not k.startswith('.local/')}
    for name in ['prepare_live_pipeline.py','Build-LivePipeline.ps1','run-live-stage.sh']:
        m['sources']['tools/pose-v1/'+name]=old.sha(root/'tools/pose-v1'/name)
    m['scope']='finite main-owned Engine plus real VPU capture and owned AU live555; no HDMI; unchanged math SDK BOOT'
    m['vendor_files']=old.load(root/'.local/pose-v1-build/owned-rtsp-20261008-r3/vendor-files.json')
    m['frozen_resident_module_sources']={k:v['sha256'] for k,v in old.load(base/'manifest.json')['build_files'].items() if k in m['build_files']}
    for key in ['frames','warmup_frames','fixed_cases','production_calls','regression_calls']:m.pop(key,None)
    shutil.copytree(base,a.output)
    shutil.copyfile(root/'tools/pose-v1/run-live-stage.sh',a.output/'run-live-stage.sh')
    (a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    (a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
    count=old.verify(a.output);print(json.dumps(dict(payloads=count,build_sources=len(m['build_files']),manifest_sha256=old.sha(a.output/'manifest.json'))))
if __name__=='__main__':main()
