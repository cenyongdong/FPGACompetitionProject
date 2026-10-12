"""Freeze the approved isolated single-context sequence and retain prior bytes."""
import json,shutil
import mixed_validation_gate as g
root=g.ROOT;base=root/'.local/pose-v1-model-vpu/package-20261010-r2';g.verify(base);m=g.load(base/'manifest.json')
m['resident_frozen_sources']={rel:item['sha256'] for rel,item in m['build_files'].items()}
old='tools/pose-v1/model-vpu-CMakeLists.txt';new='tools/pose-v1/resident-sequence-CMakeLists.txt';m['build_files'].pop(old);m['build_files'][new]=dict(destination='CMakeLists.txt',sha256=g.sha(root/new))
for rel in ['software/pose_v1/include/resident_sequence.hpp','software/pose_v1/src/resident_sequence.cpp','software/pose_v1/src/resident_sequence_selftest.cpp','software/pose_v1/src/resident_sequence_check.cpp','software/pose_v1/src/resident_producer_count_observation.cpp','software/pose_v1/src/resident_producer_count_selftest.cpp']:
    m['build_files'][rel]=dict(destination=rel.split('/')[-1],sha256=g.sha(root/rel))
for name in ['create_resident_sequence_sources.py','prepare_resident_sequence.py','Build-ResidentSequence.ps1','review_resident_sequence_build_base.py','run-resident-sequence.sh']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(root/rel)
m['build_script']='tools/pose-v1/Build-ResidentSequence.ps1'
m['resident_sequence']=dict(stages=['contracts','resident'],phase_calls=[4,103],phase_offsets=[0,4],total_calls=107,phase_period_ns=[500000000,200000000],total_seconds=180,engine_init_seconds=60,first_capture_seconds=5,encoder_limit=1000,contexts=1,producer192_rows=856,network=False,display=False,normal_source_reads_added=0)
out=root/'.local/pose-v1-resident-sequence/package-20261010-r1';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n')
print(g.verify(out),len(m['build_files']))
