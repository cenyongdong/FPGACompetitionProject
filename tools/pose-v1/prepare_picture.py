"""Freeze the reviewed picture bridge while retaining all historical sources."""
import json,shutil
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-resident-sequence/package-20261010-r1';g.verify(base);m=g.load(base/'manifest.json')
m['picture_frozen_sources']={rel:item['sha256'] for rel,item in m['build_files'].items()}
old='tools/pose-v1/resident-sequence-CMakeLists.txt';new='tools/pose-v1/picture-CMakeLists.txt';m['build_files'].pop(old);m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(root/new))
for rel in ['software/pose_v1/include/picture_source.hpp','software/pose_v1/include/picture_vpu.hpp','software/pose_v1/src/picture_source.cpp','software/pose_v1/src/picture_vpu.cpp','software/pose_v1/src/picture_marker.cpp','software/pose_v1/src/picture_source_selftest.cpp','software/pose_v1/src/picture_sequence.cpp','software/pose_v1/src/picture_sequence_selftest.cpp','software/pose_v1/src/picture_check.cpp','software/pose_v1/src/picture_reference_export.cpp']:
    m['build_files'][rel]=dict(destination=rel.split('/')[-1],sha256=g.sha(root/rel))
for name in ['create_picture_sources.py','prepare_picture.py','Build-Picture.ps1','review_picture_build_base.py','run-picture.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-Picture.ps1';m['picture']=dict(phases=[4,103],total_calls=107,phase_period_ns=[500000000,500000000],first_capture_seconds=5,engine_init_seconds=60,total_seconds=180,encoded_frame_limit=1000,publication_limit=107,queue_capacity=2,contexts=1,owned_NV12_file_limit=108,owned_NV12_bytes_max=149299200,network=False,HDMI=False,display_child=False)
out=root/'.local/pose-v1-picture/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
