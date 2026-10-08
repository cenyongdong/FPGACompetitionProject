"""Prepare fresh resident sources and independently verified27 board goldens."""
import argparse,json,shutil
from pathlib import Path
import mixed_validation_gate as old

root=old.ROOT
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
base=root/'.local/pose-v1-pipeline/package-20261008-r8';old.verify(base)
m=json.loads((base/'manifest.json').read_text())
for rel,item in m['build_files'].items():assert old.sha(root/rel)==item['sha256']
shutil.copytree(base,a.output)
for rel in ('software/pose_v1/src/vpu_startup_encoder.cpp','software/pose_v1/src/pipeline_encode_check.cpp','tools/pose-v1/pipeline-CMakeLists.txt'):del m['build_files'][rel]
new={'software/pose_v1/include/vpu_resident_encoder.hpp':'vpu_resident_encoder.hpp','software/pose_v1/include/resident_frame_queue.hpp':'resident_frame_queue.hpp','software/pose_v1/src/vpu_resident_encoder.cpp':'vpu_resident_encoder.cpp','software/pose_v1/src/resident_check.cpp':'resident_check.cpp','tools/pose-v1/resident-CMakeLists.txt':'CMakeLists.txt'}
for rel,name in new.items():m['build_files'][rel]=dict(destination=name,sha256=old.sha(root/rel))
evidence=root/'tools/pose-v1/evidence/runtime-20261007-r2/n1';count=old.verify(evidence)
rows=old.lines(evidence/'results/results.jsonl');assert len(rows)==28 and rows[0]['case']==rows[-1]['case']
for row in rows[:27]:
    for kind,size in [('scores',400),('poses',16800)]:
        src=evidence/'results'/(row['output_stem']+'.'+kind+'.f32');assert src.stat().st_size==size
        dst=a.output/'r6-reference'/(row['case']+'.'+kind+'.f32')
        if dst.exists():assert dst.read_bytes()==src.read_bytes()
        else:shutil.copyfile(src,dst)
m['reference_source']=dict(path=str(evidence.relative_to(root)),manifest_sha256=old.sha(evidence/'files.sha256'),verified_files=count)
m['scope']='finite resident workers;1000encoded maximum;20s after Engine ready;no RTSP/HDMI'
for rel in ('tools/pose-v1/Build-Resident.ps1','tools/pose-v1/resident-CMakeLists.txt','tools/pose-v1/prepare_resident_package.py'):m['sources'][rel]=old.sha(root/rel)
(a.output/'manifest.json').write_bytes((json.dumps(m,indent=2)+'\n').encode())
(a.output/'files.sha256').write_bytes(''.join(old.sha(f)+'  '+f.relative_to(a.output).as_posix()+'\n' for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='files.sha256').encode())
print('Fresh resident sources/SDK/model/27 independent board reference identities prepared:',a.output)
