"""Preserve r1 Native Werror, fix test indentation in new files only."""
import json,shutil
import mixed_validation_gate as g
r=g.ROOT;prior=r/'.local/pose-v1-read-phase/package-20261011-r1';g.verify(prior);m=g.load(prior/'manifest.json')
m['read_phase_r1_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
for name in ['read_phase_selftest','read_phase_sdk_selftest']:
    old='software/pose_v1/src/'+name+'.cpp';new='software/pose_v1/src/'+name+'_r2.cpp'
    text=(r/old).read_text(encoding='utf-8')
    text=text.replace('if(argc!=2)throw std::runtime_error("Fresh root required");','if(argc!=2){throw std::runtime_error("Fresh root required");}\n    ').replace('if(argc!=3)throw std::runtime_error("Graph/fresh evidence required");','if(argc!=3){throw std::runtime_error("Graph/fresh evidence required");}\n    ')
    assert not (r/new).exists();(r/new).write_text(text,encoding='utf-8',newline='\n')
    m['build_files'].pop(old);m['build_files'][new]=dict(destination=name+'.cpp',sha256=g.sha(r/new))
base='tools/pose-v1/review_read_phase_build_base.py';new='tools/pose-v1/review_read_phase_r2_build_base.py'
text=(r/base).read_text(encoding='utf-8').replace("'read_phase_frozen_sources')","'read_phase_frozen_sources','read_phase_r1_frozen_sources')")
assert not (r/new).exists();(r/new).write_text(text,encoding='utf-8',newline='\n')
base='tools/pose-v1/review_read_phase_stage.py';new='tools/pose-v1/review_read_phase_r2_stage.py'
text=(r/base).read_text(encoding='utf-8').replace('review_read_phase_build_base','review_read_phase_r2_build_base');assert not (r/new).exists();(r/new).write_text(text,encoding='utf-8',newline='\n')
for name in ['prepare_read_phase_r2.py','review_read_phase_r2_build_base.py','review_read_phase_r2_stage.py']:
    rel='tools/pose-v1/'+name;m['sources'][rel]=g.sha(r/rel)
out=r/'.local/pose-v1-read-phase/package-20261011-r2';assert not out.exists();shutil.copytree(prior,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n')
(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
