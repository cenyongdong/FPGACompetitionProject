"""Fresh guarded integration; frozen live orchestration and model modules."""
import argparse, json, shutil
from pathlib import Path
import mixed_validation_gate as old

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    root=old.ROOT; base=root/'.local/pose-v1-live/package-20261008-r2'
    old.verify(base); m=old.load(base/'manifest.json')
    for rel,item in m['build_files'].items():
        assert old.sha(root/rel)==item['sha256']
    for rel,digest in m['sources'].items():
        assert old.sha(root/rel)==digest
    frozen=dict(m['build_files'])
    for rel in ('software/pose_v1/src/online_rtsp.cpp','tools/pose-v1/live-CMakeLists.txt'):
        del m['build_files'][rel]
    for name in ('include/guarded_rtsp.hpp','src/guarded_rtsp.cpp','src/guarded_network_adapter.cpp'):
        rel='software/pose_v1/'+name
        m['build_files'][rel]=dict(destination=Path(name).name,sha256=old.sha(root/rel))
    rel='tools/pose-v1/guarded-live-CMakeLists.txt'
    m['build_files'][rel]=dict(destination='CMakeLists.txt',sha256=old.sha(root/rel))
    for name in ('prepare_guarded_live.py','Build-GuardedLive.ps1'):
        rel='tools/pose-v1/'+name;m['sources'][rel]=old.sha(root/rel)
    m['build_script']='tools/pose-v1/Build-GuardedLive.ps1'
    m['guarded_network']=True
    m['frozen_live_sources']={k:v['sha256'] for k,v in frozen.items()}
    m['scope']='guarded TCP send failure propagation with frozen live orchestration; explicit copies, model, SDK, VPU unchanged'
    # Both module hashes must equal the SDK-free positive/negative candidate.
    audit=old.load(root/'tools/pose-v1/evidence/guarded-normal-20261008-r1/completion-review.json')
    assert audit['status']=='SDK_free_guarded_normal_reader_control_passed' and audit['guarded_module_same_negative']
    candidate=old.load(root/'.local/pose-v1-build/guarded-normal-20261008-r1/build-result.json')
    for rel in ('software/pose_v1/include/guarded_rtsp.hpp','software/pose_v1/src/guarded_rtsp.cpp'):
        assert old.sha(root/rel)==candidate['sources'][rel]
    m['guarded_module_baseline_review_sha256']=old.sha(root/'tools/pose-v1/evidence/guarded-normal-20261008-r1/completion-review.json')
    shutil.copytree(base,args.output)
    (args.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
    (args.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(args.output).as_posix()+'\n' for f in sorted(args.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
    print(json.dumps(dict(payloads=old.verify(args.output),build_sources=len(m['build_files']),manifest_sha256=old.sha(args.output/'manifest.json'))))
if __name__=='__main__':main()
