"""Keep the frozen eight-task flush; use a separate one-task boundary ledger."""
import json,shutil
import mixed_validation_gate as g
r=g.ROOT;base=r/'.local/pose-v1-upstream-boundary/package-20261011-r3';g.verify(base);m=g.load(base/'manifest.json');m['upstream_r3_frozen_sources']={p:v['sha256'] for p,v in m['build_files'].items()}
m['build_files'].pop('software/pose_v1/src/upstream_boundary_check.cpp');rel='software/pose_v1/src/upstream_boundary_check_r4.cpp';m['build_files'][rel]=dict(destination='upstream_boundary_check.cpp',sha256=g.sha(r/rel));m['sources']['tools/pose-v1/create_upstream_boundary_r4.py']=g.sha(r/'tools/pose-v1/create_upstream_boundary_r4.py')
m['upstream_boundary']['persistence']='unchanged original8 tasks plus separate1 boundary task ledger; same frozen flush exception semantics';m['upstream_boundary']['r3_three']='4 presaved returns60400 bitwise; nine-task guard stopped all deferred saves; failure retained, no103'
out=r/'.local/pose-v1-upstream-boundary/package-20261011-r4';assert not out.exists();shutil.copytree(base,out)
(out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8',newline='\n');(out/'files.sha256').write_text(''.join(g.sha(p)+'  '+p.relative_to(out).as_posix()+'\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='files.sha256'),encoding='utf-8',newline='\n');print(g.verify(out),len(m['build_files']))
